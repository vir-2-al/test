import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from queue import Queue
import threading


class LogLvlEnum(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    EXCEPTION = "exception"
    CRITICAL = "critical"


class AsyncLogger:
    def __init__(self, **kwargs):
        """
        Async logging with queue and thread pool to prevent blocking.
        :param filename: str - Log file path (None for console)
        :param filemode: str - File mode ('a' or 'w', default 'a')
        :param level: str/int - Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        :param format: str - Log message format string
        :param datefmt: str - Date formatting string
        :param handlers: list - Custom logging handlers (overrides file settings)
        """
        self.log_queue = Queue()
        self.threadpool = ThreadPoolExecutor(max_workers=2)
        self.logger = logging.getLogger(f"AsyncLogger_{id(self)}")

        self._configure_logger(**kwargs)

        threading.Thread(target=self.__log_worker, daemon=True).start()

    def _configure_logger(self, **kwargs):
        level = kwargs.get('level', logging.WARNING)
        self.logger.setLevel(level)

        if 'handlers' in kwargs:
            for handler in kwargs['handlers']:
                self.logger.addHandler(handler)
            return

        filename = kwargs.get('filename')
        filemode = kwargs.get('filemode', 'a')
        handler = logging.FileHandler(filename, filemode) if filename else logging.StreamHandler()

        fmt = kwargs.get('format', '%(asctime)s - %(levelname)s - %(message)s')
        datefmt = kwargs.get('datefmt', None)
        formatter = logging.Formatter(fmt, datefmt)
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

    def __log_worker(self):
        logger_map = {
            LogLvlEnum.DEBUG.value: self.logger.debug,
            LogLvlEnum.INFO.value: self.logger.info,
            LogLvlEnum.WARNING.value: self.logger.warning,
            LogLvlEnum.ERROR.value: self.logger.error,
            LogLvlEnum.EXCEPTION.value: self.logger.exception,
            LogLvlEnum.CRITICAL.value: self.logger.critical
        }

        while True:
            try:
                level, msg = self.log_queue.get()
                if level in logger_map:
                    logger_map[level](msg)
                self.log_queue.task_done()
            except Exception as e:
                print(f"Logging error: {e}")

    async def __basic_logger(self, level, msg):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.threadpool, self.log_queue.put, (level, msg))

    async def debug(self, msg):
        await self.__basic_logger(LogLvlEnum.DEBUG.value, msg)

    async def info(self, msg):
        await self.__basic_logger(LogLvlEnum.INFO.value, msg)

    async def warning(self, msg):
        await self.__basic_logger(LogLvlEnum.WARNING.value, msg)

    async def error(self, msg):
        await self.__basic_logger(LogLvlEnum.ERROR.value, msg)

    async def exception(self, msg):
        await self.__basic_logger(LogLvlEnum.EXCEPTION.value, msg)

    async def critical(self, msg):
        await self.__basic_logger(LogLvlEnum.CRITICAL.value, msg)
