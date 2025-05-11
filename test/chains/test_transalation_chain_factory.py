

import src.configs.config
from loguru import logger
from src.llm_chains.translate_chain_factory import TranslateChainFactory
from src.llm.gemini_chat_model_factory import GeminiChatModelFactory

def test_translate_chain():
    llm = GeminiChatModelFactory().build()
    chain = TranslateChainFactory.create_chain(llm)
    output = chain.invoke({"text": "why sky is blue"})
    logger.info(output)