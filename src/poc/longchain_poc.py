import src.configs.config
from loguru import logger
from langchain_core.prompts import ChatPromptTemplate

from langchain_google_genai import ChatGoogleGenerativeAI as ChatAI

llm = ChatAI(
    model="gemini-2.0-flash",
    temperature=2, # 0.0-2.0
    max_tokens=10000,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    api_key=src.configs.config.yaml_configs["gemini"]["api_key"],
)
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant that translates English to Chinese."),
        ("user", "Translate this sentence from English to Chinese. {text}"),
    ]
)

chain = prompt | llm
output = chain.invoke({"text": "I love programming."})

logger.info(f"output: {output}")