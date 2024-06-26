import logging.config
import os

import yaml
from rich.console import Console
from rich.logging import RichHandler


def setup_logging() -> None:
    parent_directory = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.dirname(parent_directory)
    file_config = os.path.join(root_path, "raw_dbmodel/logging.yml")

    if not os.path.exists(file_config):
        raise FileNotFoundError("File to set config logging not exists")

    with open(file_config, 'r') as file:
        file_yml = yaml.safe_load(file)

    _formatter = file_yml['formatters']
    fmt = _formatter['fmt']
    date_fmt = _formatter['date_fmt']

    fmt_class = logging.Formatter(fmt=fmt, datefmt=date_fmt)

    logger = logging.getLogger("raw_dbmodel")
    console = Console()
    rich_handler = RichHandler(
        show_time=False,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        markup=True,
        show_path=False,
        console=console,
    )
    rich_handler.setFormatter(fmt_class)
    logger.addHandler(rich_handler)

    logger.setLevel(logging.INFO)
    logger.propagate = False
