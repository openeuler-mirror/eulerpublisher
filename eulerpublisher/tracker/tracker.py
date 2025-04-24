import pika
import json
from multiprocessing import Process
from eulerpublisher.utils.exceptions import UnsupportedArtifactType
from eulerpublisher.utils.constants import ARTIFACT_TYPES
from eulerpublisher.utils.constants import GITHUB_ACTIONS_SUCCESS
class Tracker(Process):
    def __init__(self, logger, config, db):
        super().__init__()
        self.logger = logger
        self.config = config
        self.db = db
        self.logger.info("Tracker initialized")

    def run(self):
        conn = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = conn.channel()

        channel.exchange_declare(exchange='eulerpublisher', exchange_type='topic')

        queue = channel.queue_declare(queue='', exclusive=True)
        queue_name = queue.method.queue

        channel.queue_bind(exchange='eulerpublisher', queue=queue_name, routing_key='tracker')

        def callback(ch, method, properties, body):
            request = json.loads(body)
            self.logger.info(f"Received request: {request}")
            trigger = request.get("trigger")
            artifact = request.get("artifact")
            artifact_type = artifact.get("type")
            artifact_info = artifact.get("info")
            self._handle_status(artifact_type, artifact_info)

        channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
        channel.start_consuming()

    def _handle_status(self, artifact_type, artifact_info):
        handle_functions = {
            ARTIFACT_TYPES[0]: self._handle_container_status,
            ARTIFACT_TYPES[1]: self._handle_rpm_status,
            ARTIFACT_TYPES[2]: self._handle_cloudimg_status
        }

        if artifact_type not in handle_functions:
            self.logger.error(f"Unsupported artifact type: {artifact_type}")
            raise UnsupportedArtifactType(artifact_type)
        
        handle_functions[artifact_type](artifact_info)

    def _handle_container_status(self, artifact_info):
        self.logger.info(f"Handling container status...")
        registries = artifact_info.get("registries")
        repository = artifact_info.get("repository")
        name = artifact_info.get("name")
        version = artifact_info.get("version")
        tag = artifact_info.get("tag")
        archs = artifact_info.get("archs")
        status = artifact_info.get("status")

        if status == GITHUB_ACTIONS_SUCCESS:
            for registry in registries:
                self.db.insert_image(
                    software_name=name, 
                    version_name=version,
                    arch=','.join(archs), 
                    registry=registry, 
                    repository=repository, 
                    tag=tag)

    def _handle_rpm_status(self, artifact_info):
        pass

    def _handle_cloudimg_status(self, artifact_info):
        pass