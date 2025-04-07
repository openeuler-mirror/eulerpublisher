from eulerpublisher.utils.config import Config
from eulerpublisher.utils.logger import Logger
from eulerpublisher.database.database import Database
from eulerpublisher.orchestrator.orchestrator import Orchestrator
from eulerpublisher.monitor.monitor import Monitor
from eulerpublisher.tracker.tracker import Tracker


def main():
    config = Config()
    logger = Logger(config=config)
    db = Database(config=config, logger=logger)
    orchestrator = Orchestrator(config=config, logger=logger, db=db)
    monitor = Monitor(config=config, logger=logger, db=db)
    tracker = Tracker(config=config, logger=logger, db=db)

    orchestrator.start()
    # monitor.start()
    tracker.start()
 
    try:
        orchestrator.join()
        # monitor.join()
        tracker.join()
    except KeyboardInterrupt:
        orchestrator.terminate()
        # monitor.terminate()
        tracker.terminate()
        
