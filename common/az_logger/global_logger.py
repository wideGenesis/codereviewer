import atexit
import logging
import os

from opencensus.ext.azure.log_exporter import AzureLogHandler
from logging import StreamHandler
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Set, Any


class SingletonMeta(type):
    """Метакласс для создания Singleton."""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class CustomLogger(metaclass=SingletonMeta):
    def __init__(self, azure_connection_string: Optional[str], log_level_local: str, log_level_azure: str):
        """
        Initializes the logger with AzureLogHandler if connection string is provided.
        Otherwise, defaults to a local logger.

        :param azure_connection_string: Azure connection string for logging to Azure.
        :param log_level_local: Logging level for local logger.
        :param log_level_azure: Logging level for Azure logger.
        """
        if not hasattr(self, 'initialized'):
            self.logger = logging.getLogger("custom_logger")
            self.logger.setLevel(logging.DEBUG)  # Установка уровня логирования на DEBUG

            # StreamHandler для локального логирования (stdout)
            stream_handler = StreamHandler()
            stream_handler.setLevel(self._get_log_level(log_level_local))
            stream_handler.setFormatter(self._get_formatter())
            self.logger.addHandler(stream_handler)

            # Azure Handler (если указан connection string)
            if azure_connection_string:
                azure_handler = AzureLogHandler(connection_string=azure_connection_string)
                azure_handler.setLevel(self._get_log_level(log_level_azure))
                azure_handler.setFormatter(self._get_formatter())
                self.logger.addHandler(azure_handler)

            else:
                print("Warning: Azure connection string is not provided. Defaulting to local logger only.")

            # Настройка пула потоков для асинхронного логирования
            # self.executor = ThreadPoolExecutor(max_workers=1)

            # Регистрация метода shutdown при завершении программы
            atexit.register(self.shutdown)

            # Помечаем, что логгер инициализирован
            self.initialized = True

    def _get_log_level(self, log_level: str) -> int:
        """Помощник для получения уровня логирования."""
        return getattr(logging, log_level.upper(), logging.INFO)

    def _get_formatter(self) -> logging.Formatter:
        """Возвращает форматтер для логирования сообщений."""
        return logging.Formatter(
            "[%(levelname)-3s]-"
            "[FILE: %(filename)-3s]-"
            "[FUNC: %(funcName)-3s]-"
            "[LINE: %(lineno)-3d]-[MESSAGE: %(message)s] - %(asctime)s"
        )
            # '%(asctime)s - %(levelname)s - %(message)s - '
            # 'File: %(filename)s, Func: %(funcName)s, Line: %(lineno)d, '
            # 'Module: %(module)s, Process: %(process)d, ProcessName: %(processName)s, '
            # 'Thread: %(thread)d, ThreadName: %(threadName)s',


    # def custom_dimensions_from_record(self, record: logging.LogRecord, properties: Set[str]) -> dict[str, Any]:
    #     """
    #     Создаёт словарь custom_dimensions из LogRecord.
    #
    #     :param record: Объект записи лога.
    #     :param properties: Набор свойств для включения в custom dimensions.
    #     :return: Словарь с custom dimensions.
    #     """
    #     custom_dimensions = {}
    #     for prop in properties:
    #         custom_dimensions[prop] = getattr(record, prop, 'N/A')
    #
    #     # Добавление специфичных полей
    #     custom_dimensions["message"] = record.getMessage()
    #     return custom_dimensions

    def _log_async(self, level: str, msg: str, kwargs):
        """Асинхронная функция для логирования."""
        log_level = self._get_log_level(level)

        # Собираем информацию о вызове (файл, функция, строка)
        fn, lno, func, sinfo = self.logger.findCaller(stack_info=False)

        # Создание записи лога с корректными значениями
        record = self.logger.makeRecord(
            self.logger.name, log_level, fn, lno, msg, args=None, exc_info=None, func=func
        )

        self.logger.handle(record)

    def log(self, level: str, msg: str, exc_info=False, **kwargs):
        """Логирование сообщения с опцией передачи информации об исключении."""
        log_level = self._get_log_level(level)

        # Создание записи лога с корректными значениями
        self.logger.log(log_level, msg, exc_info=exc_info, **kwargs)

    def shutdown(self):
        """Закрытие логгера при завершении работы программы."""
        pass  # В синхронной версии нет пула потоков, но можем оставить для совместимости

    # def log(self, level: str, msg: str, **kwargs):
    #     """Логирование сообщения с использованием асинхронного вызова."""
    #     self.executor.submit(self._log_async, level, msg, kwargs)

    # def shutdown(self):
    #     """Закрытие пула потоков при завершении работы программы."""
    #     self.executor.shutdown()

    # Делегирование стандартных методов логирования на внутренний логгер
    def debug(self, msg: str, **kwargs):
        self.log("debug", msg, **kwargs)

    def info(self, msg: str, **kwargs):
        self.log("info", msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        self.log("warning", msg, **kwargs)

    def error(self, msg: str, exc_info=True, **kwargs):
        self.log("error", msg, exc_info=exc_info, **kwargs)

    def exception(self, msg: str, **kwargs):
        self.log("error", msg, exc_info=True, **kwargs)

    def critical(self, msg: str, **kwargs):
        self.log("critical", msg, **kwargs)


#
#
#
# from dotenv import load_dotenv
#
# load_dotenv(dotenv_path='common_lib/settings/.env')
# conn_str = os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
#
# # Example usage:
# logger = CustomLogger(azure_connection_string=conn_str, log_level_local="debug", log_level_azure="info")
#
# try:
#     # Ваш основной код, где могут возникнуть ошибки
#     logger.info("This is an info log.")
#     # Здесь может быть бизнес-логика
#     result = 1 / 0  # Искусственно вызванная ошибка для примера
# except Exception as e:
#     # Логгируем ошибку в случае исключения
#     logger.error(f"This is an error log. {e}")
# # #
