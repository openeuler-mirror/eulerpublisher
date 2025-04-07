import logging
import os

from eulerpublisher.utils import exceptions
from eulerpublisher.utils.constants import LOG_DIR

LOG_PATH = os.path.join(LOG_DIR, "eulerpublisher.log")

class Logger:
    def __init__(self, config, log_path=LOG_PATH):
        self.config = config
        self.log_path = log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        debug = self.config.get("global", "debug")
        log_level = logging.DEBUG if debug == "True" else logging.INFO
        logging.basicConfig(
            format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s',
            filename=log_path, level=log_level, filemode='w+')
        self.logger = logging.getLogger("eulerpublisher")
        
    def info(self, message):
        self.logger.info(message)

    def debug(self, message):
        self.logger.debug(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)
        
