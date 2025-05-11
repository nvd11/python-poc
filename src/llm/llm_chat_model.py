from abc import ABC

from pyparsing import abstractmethod
from langchain_core.language_models.chat_models import BaseChatModel

class LLMChatModelFactory(ABC):
    @abstractmethod
    def build(self) -> BaseChatModel:
        pass
