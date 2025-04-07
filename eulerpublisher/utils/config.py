import configparser
import os

from eulerpublisher.utils import exceptions
from eulerpublisher.utils.constants import CONFIG_DIR

CONFIG_PATH = os.path.join(CONFIG_DIR, "eulerpublisher.conf")

class Config:
    def __init__(self, config_path=CONFIG_PATH):
        self.config = configparser.ConfigParser()
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        if not os.path.exists(config_path):
            raise exceptions.NoSuchFile(config_path)
        self.config_path = config_path
        self.config.read(self.config_path)

    def get(self, section, option):
        return self.config.get(section, option)