from multiprocessing import Process


class Monitor(Process):
    def __init__(self, logger, config, db):
        self.logger = logger
        self.config = config
        self.db = db
        self.logger.info("Monitor initialized")

    
    def fetch_versions(self, software_name):
        pass

    def filter_versions(self, software_name, versions):
        pass