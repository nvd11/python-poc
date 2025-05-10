import src.configs.config
from loguru import logger

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda, RunnableBranch



# 1. 初始化 LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.2,  # 调整 temperature 以获得更稳定的翻译
    max_tokens=1000,
    api_key=src.configs.config.yaml_configs["gemini"]["api_key"],
)
# --- 示例 1: 并行处理后合并 (Fork-Join) ---
print("\n--- 示例 1: 并行处理后合并 (Fork-Join) ---")

# 假设我们想为一个主题并行生成：定义、优点、缺点
# 然后将它们合并成一个报告

# 定义生成器
definition_prompt = ChatPromptTemplate.from_template("请用一句话简洁地定义 '{topic}'。")
advantages_prompt = ChatPromptTemplate.from_template("列出 '{topic}' 的3个主要优点。")
disadvantages_prompt = ChatPromptTemplate.from_template("列出 '{topic}' 的3个主要缺点。")

# 单个处理链
definition_chain = definition_prompt | llm | StrOutputParser()
advantages_chain = advantages_prompt | llm | StrOutputParser()
disadvantages_chain = disadvantages_prompt | llm | StrOutputParser()

# 使用 RunnableParallel 来“分叉”
# RunnableParallel 会将输入 ({"topic": "..."}) 传递给每个子链
# 并将它们的输出收集到一个字典中，键是 RunnableParallel 中定义的键
parallel_chains = RunnableParallel(
    definition=definition_chain,
    advantages=advantages_chain,
    disadvantages=disadvantages_chain,
)

# "合并" 链：接收 parallel_chains 的输出字典，并生成报告
report_prompt = ChatPromptTemplate.from_template(
    """
    根据以下信息生成一份关于 '{topic}' 的简要报告:

    定义:
    {definition}

    优点:
    {advantages}

    缺点:
    {disadvantages}

    ---
    综合报告:
    """
)
report_chain = report_prompt | llm | StrOutputParser()

# 完整的 fork-join 链
# 输入 {"topic": "..."}
# 1. parallel_chains 会接收 {"topic": "..."}
#    - definition_chain 接收 {"topic": "..."} 输出字符串
#    - advantages_chain 接收 {"topic": "..."} 输出字符串
#    - disadvantages_chain 接收 {"topic": "..."} 输出字符串
#    parallel_chains 的输出是 {"definition": "...", "advantages": "...", "disadvantages": "..."}
# 2. 这个输出字典会传递给 report_chain。
#    report_chain 的 prompt 需要 'topic', 'definition', 'advantages', 'disadvantages'
#    所以我们需要确保 'topic' 也传递给了 report_chain。
#    我们可以通过 RunnablePassthrough.assign() 来添加原始的 topic，或者让 parallel_chains 也输出 topic。

# 方式一: 修改 parallel_chains，让它也传递 topic
# parallel_chains_with_topic = RunnableParallel(
#     definition=definition_chain,
#     advantages=advantages_chain,
#     disadvantages=disadvantages_chain,
#     topic=RunnablePassthrough() # 这会把整个输入字典（包含topic）作为 'topic' 键的值，可能不是想要的
# )
# 更准确的是：
# topic_passthrough = RunnablePassthrough.assign(topic=lambda x: x["topic"]) # 确保topic字段被正确提取

# 方式二: 使用 RunnablePassthrough 在 parallel_chains 之后添加 topic
# 这是更常见的模式，当 parallel_chains 的输出不包含所有下游需要的字段时
# 我们希望 report_prompt 能接收到原始的 topic 以及并行生成的内容
# RunnablePassthrough() 会将完整的输入传递下去
# RunnablePassthrough.assign(...) 允许我们构建一个新的字典，包含原始输入和新计算的值

# 最终链：
# 1. 原始输入: {"topic": "..."}
# 2. RunnablePassthrough.assign(...):
#    - `gathered_info`: 执行 parallel_chains，其输入是原始输入 {"topic": "..."}。输出是 {"definition": ..., "advantages": ..., "disadvantages": ...}
#    - 原始的 `topic` 会被保留 (因为 assign 是合并字典)
#    所以，RunnablePassthrough.assign 的输出会是:
#    {"topic": "...", "gathered_info": {"definition": ..., "advantages": ..., "disadvantages": ...}}
#    这还不是 report_prompt 想要的格式。

# 正确的组合方式:
# 我们希望 parallel_chains 的输出 (一个字典) 和原始的 topic 一起传给 report_prompt
# 方法1: 让 parallel_chains 也输出 topic (如果简单)
# parallel_chains = RunnableParallel(
#     definition=definition_chain,
#     advantages=advantages_chain,
#     disadvantages=disadvantages_chain,
#     topic=lambda x: x['topic'] # 将 topic 传递下去
# )
# full_fork_join_chain = parallel_chains | report_chain
# 这种方式下，report_prompt 会接收到 {"definition": ..., "advantages": ..., "disadvantages": ..., "topic": ...}，这很好。

# 方法2: 更通用的，先运行 parallel，然后将结果和原始输入结合
# (这是一个更高级的用法，当并行步骤的输出需要与原始输入中的其他字段混合时)
# 这里我们用一个更直接的LCEL方式：
# RunnableParallel 本身可以接受一个字典，它的值是runnables。
# 它会把自己的输入传递给所有这些runnables。
# 它的输出是一个字典，key是RunnableParallel定义的key，value是对应runnable的输出。

# 假设输入是: {"user_topic": "AI in education"}
# 我们希望 parallel_chains 的输入是 {"topic": "AI in education"}
# report_chain 的输入是 {"topic": "AI in education", "definition": "...", "advantages": "...", "disadvantages": "..."}

map_input_to_topic = RunnableLambda(lambda x: {"topic": x["user_topic"]})

# parallel_chains 已经定义好了，它期望输入 {"topic": ...}
# 它的输出是 {"definition": ..., "advantages": ..., "disadvantages": ...}

# 我们需要将 parallel_chains 的输出和原始的 topic 合并，再传给 report_chain
# 这可以通过 RunnablePassthrough.assign 实现
# 假设 report_prompt 的输入变量是 {topic_for_report}, {definition}, {advantages}, {disadvantages}

# 最简洁的方式是让 report_chain 直接消费 parallel_chains 的输出，并把 topic 传递过去
# parallel_chains 的输入是 {"topic": "some_topic"}
# parallel_chains 的输出是 {"definition": "def_text", "advantages": "adv_text", "disadvantages": "dis_text"}

# 为了将 "topic" 传递给 report_chain，我们可以这样做：
# 1. 原始输入: {"input_topic": "AI in education"}
# 2. (RunnablePassthrough.assign) 创建一个包含 "topic" 和 "gathered_parts" 的字典
#    "topic" 来自原始输入
#    "gathered_parts" 是 parallel_chains 的结果
# 3. (RunnableLambda) 将这个字典扁平化为 report_prompt 需要的格式

# 更简单的LCEL原生方式：
# 1. 准备 parallel_chains (已完成)
# 2. 准备 report_chain (已完成, 它需要 topic, definition, advantages, disadvantages)
# 3. 构造一个能提供这些输入的 Runnable

# 假设我们的初始输入是 {"user_topic": "AI in education"}
# 我们需要将它转换为 {"topic": "AI in education"} 给 parallel_chains
# 然后将 {"topic": "AI in education"} 和 parallel_chains 的输出一起给 report_chain

# 这是一个常见的模式：
# input_data = {"user_topic": "AI in education"}
# chain = {
#     "topic": lambda x: x["user_topic"], # 从输入中提取 topic
#     "gathered": map_input_to_topic | parallel_chains # 执行并行链
# } | RunnableLambda(lambda x: {**x["gathered"], "topic": x["topic"]}) | report_chain # 合并并送入报告链

# 让我们简化一下，假设 report_prompt 中的 topic 变量名就是 "topic"
# 并且我们确保 parallel_chains 的输入是 {"topic": "..."}
# 并且 report_chain 需要 {"topic": "...", "definition": "...", "advantages": "...", "disadvantages": "..."}

# 链式结构：
# 1. 接受 {"user_topic": "some_topic"}
# 2. 转换成 {"topic": "some_topic"} (因为所有子链都用 "topic")
# 3. 执行 parallel_chains，它输出 {"definition": ..., "advantages": ..., "disadvantages": ...}
# 4. 将 {"topic": "some_topic"} 和 上一步的输出合并，送入 report_chain

# 构造一个中间的 Runnable，它运行 parallel_chains 并保留原始的 topic
# context_aggregator 会接收 {"topic": "..."}
# 它会运行 parallel_chains (输入也是 {"topic": "..."})
# 然后将 parallel_chains 的输出与原始的 "topic" 合并
context_aggregator = RunnablePassthrough.assign(
    extracted_parts=parallel_chains # parallel_chains 会接收到 RunnablePassthrough 的整个输入
)
# context_aggregator 的输出会是:
# {
#   "topic": "...", (来自原始输入)
#   "extracted_parts": {"definition": "...", "advantages": "...", "disadvantages": "..."}
# }

# 现在我们需要将这个结构转换为 report_prompt 期望的扁平结构
# report_prompt 需要: topic, definition, advantages, disadvantages
final_formatter = RunnableLambda(
    lambda x: {
        "topic": x["topic"],
        "definition": x["extracted_parts"]["definition"],
        "advantages": x["extracted_parts"]["advantages"],
        "disadvantages": x["extracted_parts"]["disadvantages"],
    }
)

full_fork_join_chain = (
    {"topic": RunnablePassthrough()} # 假设输入是字符串 "AI in education"
    # 如果输入是 {"user_topic": "AI in education"}, 则 {"topic": lambda x: x["user_topic"]}
    | context_aggregator
    | final_formatter
    | report_chain
)

# 测试 fork-join 链
print("测试 Fork-Join 链:")
topic_to_analyze = "可再生能源"
# 输入给 full_fork_join_chain 的是字符串 topic_to_analyze
# 因为第一步是 {"topic": RunnablePassthrough()}，它会将字符串包装成 {"topic": "可再生能源"}
report = full_fork_join_chain.invoke(topic_to_analyze)
print(f"关于 '{topic_to_analyze}' 的报告:\n{report}")

# --- 示例 2: 条件分叉 (RunnableBranch) ---
print("\n--- 示例 2: 条件分叉 (RunnableBranch) ---")

# 根据输入文本的情感，给出不同的回应
sentiment_analyzer_prompt = ChatPromptTemplate.from_template(
    "分析以下文本的情感 (正面/负面/中性): '{text}'. 只回答 '正面', '负面', 或 '中性'."
)
sentiment_analyzer_chain = sentiment_analyzer_prompt | llm | StrOutputParser()

positive_response_prompt = ChatPromptTemplate.from_template("太棒了！听到关于 '{original_text}' 的正面消息总是好的。")
negative_response_prompt = ChatPromptTemplate.from_template("听到关于 '{original_text}' 的负面消息，我感到很遗憾。有什么我可以帮忙的吗？")
neutral_response_prompt = ChatPromptTemplate.from_template("感谢分享关于 '{original_text}' 的信息。")

positive_chain = positive_response_prompt | llm | StrOutputParser()
negative_chain = negative_response_prompt | llm | StrOutputParser()
neutral_chain = neutral_response_prompt | llm | StrOutputParser()

# RunnableBranch 需要一个 (condition, runnable) 对的列表，以及一个可选的 default runnable
# condition 是一个 Runnable，它接收分支的输入，并返回 True/False
# 或者是一个接收输入并返回 bool 的函数
# RunnableBranch 的输入会传递给 condition 和被选中的 runnable

# 我们需要将原始文本和分析出的情感都传递给分支逻辑
# 1. 输入: {"user_text": "..."}
# 2. 分析情感: sentiment_analyzer_chain (输入 {"text": user_text}) -> 输出 "正面" / "负面" / "中性"
# 3. 将情感和原始文本传递给 RunnableBranch
# 4. RunnableBranch 根据情感选择路径，选中的路径需要原始文本

# 构建一个传递原始文本和情感的上下文
conditional_context_chain = RunnablePassthrough.assign(
    sentiment=RunnableLambda(lambda x: {"text": x["user_text"]}) | sentiment_analyzer_chain
)
# conditional_context_chain 的输入: {"user_text": "some user text"}
# conditional_context_chain 的输出: {"user_text": "some user text", "sentiment": "正面/负面/中性"}

# 条件逻辑函数，它们会接收 conditional_context_chain 的输出
def is_positive(input_dict):
    return "正面" in input_dict["sentiment"]

def is_negative(input_dict):
    return "负面" in input_dict["sentiment"]

# 分支的 Runnable 也需要原始文本，它们会接收 conditional_context_chain 的输出
# 所以它们的 prompt 需要使用 "user_text" 而不是 "original_text"
# 或者我们修改传递给它们的字典
def format_for_response_chains(input_dict):
    return {"original_text": input_dict["user_text"]}

branch = RunnableBranch(
    (is_positive, RunnableLambda(format_for_response_chains) | positive_chain),
    (is_negative, RunnableLambda(format_for_response_chains) | negative_chain),
    RunnableLambda(format_for_response_chains) | neutral_chain  # 默认分支
)

full_conditional_chain = conditional_context_chain | branch

# 测试条件链
print("\n测试条件链:")
text1 = "我今天非常开心，阳光明媚！"
text2 = "项目失败了，我很沮丧。"
text3 = "会议将在下午三点开始。"

response1 = full_conditional_chain.invoke({"user_text": text1})
print(f"输入: '{text1}'\n回应: {response1}\n")

response2 = full_conditional_chain.invoke({"user_text": text2})
print(f"输入: '{text2}'\n回应: {response2}\n")

response3 = full_conditional_chain.invoke({"user_text": text3})
print(f"输入: '{text3}'\n回应: {response3}\n")