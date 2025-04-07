from orchestrator.workflow.workflow_handler import WorkflowHandler

class JenkinsHandler(WorkflowHandler):
    def __init__(self, config, logger, db):
        self.config = config
        self.logger = logger
        self.db = db
        self.logger.info("Jenkins Handler initialized")