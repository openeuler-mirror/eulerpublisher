import logging
import os
import inspect
import sys
import colorlog

from eulerpublisher.utils import exceptions
from eulerpublisher.utils.constants import LOG_DIR

LOG_PATH = os.path.join(LOG_DIR, "eulerpublisher.log")

class CustomAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        stack = inspect.stack()
        found = False
        
        for frame in stack:
            if 'logger.py' not in frame.filename and '__init__.py' not in frame.filename:
                module_path = frame.filename
                lineno = frame.lineno
                found = True
                break
        
        if not found:
            for frame in stack:
                if 'logger.py' not in frame.filename:
                    module_path = frame.filename
                    lineno = frame.lineno
                    break
            else:
                module_path = stack[0].filename
                lineno = stack[0].lineno
        
        filename = os.path.basename(module_path)
        
        extra = kwargs.get('extra', {})
        extra.update({
            'custom_filename': filename,
            'custom_lineno': lineno
        })
        kwargs['extra'] = extra
        
        return msg, kwargs
    
class Logger:
    def __init__(self, config, log_path=LOG_PATH):
        self.config = config
        self.log_path = log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        debug = self.config.get("global", "debug")
        log_level = logging.DEBUG if debug == "True" else logging.INFO

        logger = logging.getLogger("eulerpublisher")
        logger.setLevel(log_level)
        
        if logger.handlers:
            for handler in logger.handlers:
                logger.removeHandler(handler)
                
        file_handler = logging.FileHandler(log_path, mode='w+')
        file_formatter = logging.Formatter('%(asctime)s - %(custom_filename)s[line:%(custom_lineno)d] - %(levelname)s: %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(custom_filename)s[line:%(custom_lineno)d] - %(levelname)s:%(reset)s %(message)s',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
            secondary_log_colors={},
            style='%'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        logger.propagate = False
            
        self.logger = CustomAdapter(logger, {})
        
    def info(self, message):
        self.logger.info(message)

    def debug(self, message):
        self.logger.debug(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)