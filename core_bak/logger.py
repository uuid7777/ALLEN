"""Allen 日志系统"""
import logging
from logging.handlers import RotatingFileHandler
import threading
import os


class ThreadLoggerManager:
    _loggers = {}
    _lock = threading.Lock()

    def __init__(self, log_file='./allen_log.md', level=logging.INFO):
        self.log_file = log_file
        self.level = level
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

    def get_logger(self):
        thread_id = threading.get_ident()
        key = (thread_id, self.log_file)
        with self._lock:
            if key not in self._loggers:
                logger = logging.getLogger(f'Allen-{thread_id}')
                logger.setLevel(self.level)
                if not logger.handlers:
                    handler = RotatingFileHandler(
                        self.log_file, maxBytes=10 * 1024 * 1024, backupCount=5
                    )
                    handler.setFormatter(logging.Formatter('%(message)s'))
                    handler.setLevel(self.level)
                    logger.addHandler(handler)
                self._loggers[key] = logger
        return self._loggers[key]

    def log(self, message, level=logging.INFO):
        self.get_logger().log(level, message)
