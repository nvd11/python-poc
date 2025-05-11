import src.configs.config
from loguru import logger
from src.llm.gemini_chat_model_factory import GeminiChatModelFactory


from langchain_core.language_models.chat_models import BaseChatModel

def test1_create_model():
    logger.info("test1_create_model")

    factory = GeminiChatModelFactory()
    model: BaseChatModel = factory.build()
    assert model is not None
    assert isinstance(model, BaseChatModel)

    rs = model.invoke("why sky is blue?")  # invoke means call， generate response
    assert rs is not None