import logging.config
import os

parent_directory = os.path.dirname(os.path.abspath(__name__))
root_path = os.path.dirname(parent_directory)

logging.config.fileConfig(os.path.join(root_path, "raw_dbmodel/logging.conf"))
logger = logging.getLogger("raw_dbmodel")
