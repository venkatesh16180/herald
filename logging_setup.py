import logging, logging.handlers
from config import LOG_LEVEL, LOG_PATH

_configured = False

def get_logger(name: str) -> logging.Logger:
    global _configured
    if not _configured:
        root = logging.getLogger()
        root.setLevel(LOG_LEVEL)
        fmt = logging.Formatter('%(asctime)s %(levelname)-8s %(name)s: %(message)s')
        console = logging.StreamHandler()
        console.setFormatter(fmt)
        root.addHandler(console)
        fh = logging.handlers.RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=3)
        fh.setFormatter(fmt)
        root.addHandler(fh)
        logging.getLogger('httpx').setLevel(logging.WARNING)
        _configured = True
    return logging.getLogger(name)