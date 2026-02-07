import os
import sys
import yaml
import logging
import logging.config
from pathlib import Path

def init_logging():
    with (open("shared/utils/logger/log_config.yaml", "r", encoding="utf-8")
          as f):
        config = yaml.safe_load(f)
        logging.config.dictConfig(config)

init_logging()
log = logging.getLogger()


