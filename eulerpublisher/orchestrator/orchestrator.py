import pika
import json
from multiprocessing import Process
from eulerpublisher.utils.exceptions import UnsupportedWorkflowType
from eulerpublisher.utils.constants import WORKFLOW_TYPES

class Orchestrator(Process):
    def __init__(self, logger, config, db):
        super().__init__()
        self.logger = logger
        self.config = config
        self.db = db
        self.workflow_handler = self._get_workflow_handler()
        self.logger.info("Orchestrator initialized")
        
    def _get_workflow_handler(self):
        workflow_type = self.config.get("global", "workflow_type")
        if workflow_type == WORKFLOW_TYPES[0]:
            from eulerpublisher.orchestrator.workflow.github_actions_handler import GithubActionsHandler
            return GithubActionsHandler(self.config, self.logger, self.db)
        elif workflow_type == WORKFLOW_TYPES[1]:
            from eulerpublisher.orchestrator.workflow.codearts_handler import CodeArtsHandler
            return CodeArtsHandler(self.config, self.logger, self.db)
        elif workflow_type == WORKFLOW_TYPES[2]:
            from eulerpublisher.orchestrator.workflow.jenkins_handler import JenkinsHandler
            return JenkinsHandler(self.config, self.logger, self.db)
        else:
            self.logger.error(f"Unsupported workflow type: {workflow_type}")
            raise UnsupportedWorkflowType(workflow_type)

    def run(self):
        conn = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = conn.channel()
        channel.exchange_declare(exchange='eulerpublisher', exchange_type='topic')

        queue = channel.queue_declare(queue='', exclusive=True)
        queue_name = queue.method.queue
        channel.queue_bind(exchange='eulerpublisher', queue=queue_name, routing_key='orchestrator')

        def callback(ch, method, properties, body):
            request = json.loads(body)
            self.logger.info(f"Received request: {request}")
            trigger = request.get("trigger")
            artifact = request.get("artifact")
            artifact_type = artifact.get("type")
            artifact_info = artifact.get("info")
            self.workflow_handler.handle_workflow(artifact_type, artifact_info)
            self.workflow_handler.upload_workflow()
            
        channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
        channel.start_consuming()
    
    