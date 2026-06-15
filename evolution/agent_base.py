from abc import ABC, abstractmethod
from core.llm import OPENAI_MODEL
from core.logger import ThreadLoggerManager


class AgentSystem(ABC):
    def __init__(
        self,
        model=OPENAI_MODEL,
        chat_history_file='./outputs/chat_history.md',
    ):
        self.model = model
        self.logger_manager = ThreadLoggerManager(log_file=chat_history_file)
        self.log = self.logger_manager.log
        with open(chat_history_file, 'w') as f:
            f.write('')

    @abstractmethod
    def forward(self, *args, **kwargs):
        pass
