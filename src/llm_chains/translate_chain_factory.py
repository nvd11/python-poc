import src.configs.config
from loguru import logger
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class TranslateChainFactory():

    @staticmethod
    def create_chain(llm, from_language="English", to_language="Chinese"):
        
        # define a prompt
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a helpful assistant that translates English to Chinese."),
                ("user", f"Translate this sentence from {from_language} to {to_language}. {{text}}"),
            ]
        )

        # define a parser
        output_parser = StrOutputParser()

        # 构建链
        chain = prompt | llm | output_parser
        return chain