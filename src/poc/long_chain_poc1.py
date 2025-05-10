import src.configs.config
from loguru import logger

import os
from dotenv import load_dotenv

from typing import List
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI as ChatAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.output_parsers import PydanticOutputParser
# from langchain_core.pydantic_v1 import BaseModel as V1BaseModel, Field as V1Field # For PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel

# PydanticOutputParser 需要 Pydantic v1 模型
# 如果你的 langchain_core 版本较新，可以直接用 pydantic.BaseModel
# 但为了兼容性，这里明确使用 langchain_core.pydantic_v1
class ExtractedInfo(BaseModel):
    """从文本中提取的关键信息"""
    people: List[str] = Field(description="文本中提到的人物列表")
    locations: List[str] = Field(description="文本中提到的地点列表")
    event_theme: str = Field(description="文本描述的事件主题或核心内容")

# 0. 设置环境 (确保你的 .env 文件中有 OPENAI_API_KEY)
load_dotenv()
# os.environ["OPENAI_API_KEY"] = "sk-your-api-key" # 或者直接设置

# 1. 初始化 LLM
llm = ChatAI(
    model="gemini-2.0-flash",
    temperature=2, # 0.0-2.0
    max_tokens=10000,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    api_key=src.configs.config.yaml_configs["gemini"]["api_key"],
)

# --- 链的第一部分：提取信息 ---

# 1.1 Pydantic 输出解析器
info_parser = JsonOutputParser(pydantic_object=ExtractedInfo)
# 在较新版本 langchain_core 中，可以直接用 PydanticOutputParser(pydantic_object=ExtractedInfo)
# 但 JsonOutputParser(pydantic_object=...) 行为类似，且更通用

# 1.2 提取信息的提示模板
extraction_prompt_template = ChatPromptTemplate.from_template(
    """
    请从以下文本中提取关键信息。
    文本内容:
    ```{text_input}```

    请严格按照以下JSON格式进行输出，不要添加任何额外的解释或引言:
    {format_instructions}
    """
)

# 1.3 构建信息提取链
# RunnablePassthrough.assign(text_input=lambda x: x["text_input"]) 确保 text_input 字段被正确传递
# 如果你的输入字典已经是 {"text_input": "some_text"}, 就不需要这个 assign
# 但为了明确和健壮性，可以加上
extraction_chain = (
    RunnablePassthrough.assign(
        format_instructions=lambda x: info_parser.get_format_instructions()
    )
    | extraction_prompt_template
    | llm
    | info_parser
)

# --- 链的第二部分：生成摘要 ---

# 2.1 生成摘要的提示模板
summary_prompt_template = ChatPromptTemplate.from_template(
    """
    你是一个优秀的摘要生成助手。
    根据以下提取的关键信息，生成一段关于该事件的简短摘要 (大约50-100字)。
    
    关键信息:
    人物: {people}
    地点: {locations}
    事件主题: {event_theme}

    生成的摘要:
    """
)

# 2.2 构建摘要生成链 (它接收 extraction_chain 的输出)
summary_chain = summary_prompt_template | llm | StrOutputParser()


# --- 组合成完整长链 ---
# extraction_chain 的输出 (一个 ExtractedInfo 对象的字典形式) 会作为 summary_chain 的输入
# summary_prompt_template 会自动从这个字典中获取 people, locations, event_theme
full_chain = extraction_chain | summary_chain

# --- 测试长链 ---
if __name__ == "__main__":
    event_description = "昨天下午，张三和李四在北京的科技园参加了一个关于人工智能未来发展的重要会议。会议讨论了AI在医疗和教育领域的应用前景。"
    
    print("--- 原始输入 ---")
    print(event_description)
    print("\n--- 运行长链 ---")

    # 运行整个链
    # 输入需要符合 extraction_prompt_template 中期望的键，即 "text_input"
    # 或者，如果 extraction_chain 的第一个 RunnablePassthrough.assign 修改了，按修改后的来
    # 这里我们直接使用 extraction_prompt_template 的输入格式
    
    # 为了演示中间步骤，我们可以分开调用
    print("\n--- 步骤1: 信息提取 (extraction_chain) ---")
    # extraction_chain 的输入是 {"text_input": "..."}
    extracted_data = extraction_chain.invoke({"text_input": event_description})
    print(f"提取到的结构化信息: {extracted_data}")
    
    # exit program 
    exit(0)
    print("\n--- 步骤2: 生成摘要 (summary_chain using extracted_data) ---")
    # summary_chain 的输入是 extraction_chain 的输出
    final_summary = summary_chain.invoke(extracted_data) # extracted_data 是一个字典
    print(f"生成的摘要: {final_summary}")

    print("\n--- 直接运行完整长链 (full_chain) ---")
    # full_chain 的输入是 extraction_chain 的输入
    final_summary_direct = full_chain.invoke({"text_input": event_description})
    print(f"生成的摘要 (通过 full_chain): {final_summary_direct}")

    print("\n--- 查看长链结构 (可选) ---")
    # full_chain.get_graph().print_ascii() # 需要安装 graphviz 和 pygraphviz

    # 另一个例子
    print("\n--- 另一个例子 ---")
    event_description_2 = "The G7 summit, attended by leaders like Joe Biden and Emmanuel Macron, was held in Hiroshima last May to discuss global economic stability and climate change."
    final_summary_2 = full_chain.invoke({"text_input": event_description_2})
    print(f"输入: {event_description_2}")
    print(f"生成的摘要: {final_summary_2}")