"""
Simple logging module for tracking and displaying messages with different statuses.

The logger is used to report messages and provide a structured way to log events and errors in the application.
Logging output is shown in the standard admin page. To access the logger during algorithm execution,
use the `get_logger` function from the `algomancy_utils` module.

EXAMPLE:
    >>> from algomancy_utils import Logger, get_logger
    >>> logger: Logger = get_logger()
    ...
    >>> logger.log("This is a test message")
    >>> logger.success("This is a test message")
    >>> logger.warning("This is a test message")
"""

import datetime
import traceback
from enum import StrEnum, auto
from typing import List, Optional


class MessageStatus(StrEnum):
    """
    Enum representing the status of a log message.
    """

    #: Informational message
    INFO = auto()

    #: Successful operation message
    SUCCESS = auto()

    #: Warning message for potential issues
    WARNING = auto()

    #: Error message for failed operations
    ERROR = auto()


class Message:
    """
    Representation of a single log message with metadata and formatting.

    Args:
        message: The text content of the message.
        status: The severity or type of the message. Defaults to MessageStatus.INFO.
    """

    RESET = "\033[0m"
    GREEN = "\033[92m"
    ORANGE = "\033[93m"
    RED = "\033[91m"

    def __init__(
        self, message: str, status: MessageStatus = MessageStatus.INFO
    ) -> None:
        self.message = message
        self.status = status
        self.timestamp = datetime.datetime.now()

    def __str__(self):
        """
        Returns a formatted string representation of the message with its timestamp and status.
        """
        return f"[{self.timestamp.isoformat()}] {self.status.name.rjust(7)}: {self.message}"

    def print(self):
        """
        Prints the formatted message to the console with ANSI color codes based on its status.
        """
        match self.status:
            case MessageStatus.INFO:
                print(f"{self.RESET}{self.__str__()}")
            case MessageStatus.SUCCESS:
                print(f"{self.GREEN}{self.__str__()}")
            case MessageStatus.WARNING:
                print(f"{self.ORANGE}{self.__str__()}")
            case MessageStatus.ERROR:
                print(f"{self.RED}{self.__str__()}")
            case _:
                print(f"{self.__str__()}")


class Logger:
    """
    A logger that stores and manages a collection of log messages.
    """

    def __init__(self) -> None:
        self._logs: List[Message] = []
        self.latest_log: Optional[Message] = None
        self._print_to_console = True

    def toggle_print_to_console(self, value: bool = None) -> None:
        """
        Toggles or sets whether log messages should be printed to the console.

        Args:
            value: Optional boolean to explicitly set the console printing state.
                If None, the state is toggled.
        """
        if not value:
            value = not self._print_to_console

        self._print_to_console = value

    def log(self, message: str, status: MessageStatus = MessageStatus.INFO) -> None:
        """
        Adds a new log message and prints it to the console if enabled.

        Args:
            message: The message text to log.
            status: The status/type of the message. Defaults to MessageStatus.INFO.
        """
        self._logs.append(Message(message=message, status=status))
        self.latest_log = self._logs[-1]

        if self._print_to_console:
            self.latest_log.print()

    def success(self, message: str):
        """
        Logs a success message.
        """
        self.log(message, status=MessageStatus.SUCCESS)

    def warning(self, message: str):
        """
        Logs a warning message.
        """
        self.log(message, status=MessageStatus.WARNING)

    def error(self, message: str):
        """
        Logs an error message.
        """
        self.log(message, status=MessageStatus.ERROR)

    def get_logs(self, status_filter: Optional[MessageStatus] = None) -> List[Message]:
        """
        Retrieves all stored logs, optionally filtered by status.

        Args:
            status_filter: Optional status to filter logs by.

        Returns:
            A list of Message objects.
        """
        if status_filter:
            return [log for log in self._logs if log.status == status_filter]
        return list(self._logs)

    def clear(self) -> None:
        """
        Removes all stored logs.
        """
        self._logs.clear()

    def log_traceback(self, e: Exception):
        """
        Logs the traceback of a given exception as error messages.

        Args:
            e: The exception to log the traceback for.
        """
        self.error(f"An error occurred: {e.__class__.__name__}: {e}")
        for msg in traceback.format_tb(e.__traceback__):
            self.error(msg)


def get_logger() -> Logger:
    """
    Retrieves the global logger instance.

    WARNING:
        This function is not yet implemented.

    Returns:
        The global Logger instance.
    """
    pass
