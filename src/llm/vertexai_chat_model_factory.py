from src.llm.llm_chat_model import LLMChatModelFactory
from langchain_core.language_models import BaseChatModel
from langchain_google_vertexai import ChatVertexAI
import sys

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

class VertexAIChatModelFactory(LLMChatModelFactory):
    def __init__(self):
        pass

    @override
    def build(self) -> BaseChatModel:
        llm = ChatVertexAI(model_name="gemini-1.0-pro-001")
        return llm
