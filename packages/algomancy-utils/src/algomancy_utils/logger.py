import datetime
import traceback
from enum import StrEnum, auto
from typing import List, Optional


class MessageStatus(StrEnum):
    INFO = auto()
    SUCCESS = auto()
    WARNING = auto()
    ERROR = auto()


class Message:
    def __init__(
        self, message: str, status: MessageStatus = MessageStatus.INFO
    ) -> None:
        self.message = message
        self.status = status
        self.timestamp = datetime.datetime.now()

    def __str__(self):
        return f"[{self.timestamp.isoformat()}] {self.status.name.rjust(7)}: {self.message}"

    def print(self):
        RESET = "\033[0m"
        GREEN = "\033[92m"
        ORANGE = "\033[93m"
        RED = "\033[91m"

        match self.status:
            case MessageStatus.INFO:
                print(f"{RESET}{self.__str__()}")
            case MessageStatus.SUCCESS:
                print(f"{GREEN}{self.__str__()}")
            case MessageStatus.WARNING:
                print(f"{ORANGE}{self.__str__()}")
            case MessageStatus.ERROR:
                print(f"{RED}{self.__str__()}")
            case _:
                print(f"{self.__str__()}")


class Logger:
    """
    Eenvoudige logger die berichten opslaat met status en timestamp.
    """

    def __init__(self) -> None:
        self._logs: List[Message] = []
        self.latest_log: Optional[Message] = None
        self._print_to_console = True

    def toggle_print_to_console(self, value: bool = None) -> None:
        if not value:
            value = not self._print_to_console

        self._print_to_console = value

    def log(self, message: str, status: MessageStatus = MessageStatus.INFO) -> None:
        """
        Voeg een logbericht toe.

        :param message: Het bericht dat gelogd wordt
        :param status: Status/type van het bericht (bijv. 'info', 'success', 'warning', 'error')
        """
        self._logs.append(Message(message=message, status=status))
        self.latest_log = self._logs[-1]

        if self._print_to_console:
            self.latest_log.print()

    def success(self, message: str):
        self.log(message, status=MessageStatus.SUCCESS)

    def warning(self, message: str):
        self.log(message, status=MessageStatus.WARNING)

    def error(self, message: str):
        self.log(message, status=MessageStatus.ERROR)

    def get_logs(self, status_filter: Optional[MessageStatus] = None) -> List[Message]:
        """
        Haal alle logs op, eventueel gefilterd op status.

        :param status_filter: Optioneel, filter op status (bijv. 'info')
        :return: Lijst van logs (dicts)
        """
        if status_filter:
            return [log for log in self._logs if log.status == status_filter]
        return list(self._logs)

    def clear(self) -> None:
        """
        Verwijdert alle opgeslagen logs.
        """
        self._logs.clear()

    def log_traceback(self, e: Exception):
        self.error(f"An error occurred: {e.__class__.__name__}: {e}")
        for msg in traceback.format_tb(e.__traceback__):
            self.error(msg)
