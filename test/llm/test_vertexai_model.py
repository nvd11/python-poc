import src.configs.config
from loguru import logger
from src.llm.vertexai_chat_model_factory import VertexAIChatModelFactory
from langchain_core.language_models.chat_models import BaseChatModel

def test_create_vertexai_model():
    logger.info("test_create_vertexai_model")

    factory = VertexAIChatModelFactory()
    model: BaseChatModel = factory.build()
    assert model is not None
    assert isinstance(model, BaseChatModel)

    rs = model.invoke("why sky is blue?")
    assert rs is not None
