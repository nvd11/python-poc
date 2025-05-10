import src.configs.config
from loguru import logger
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI as ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from google.cloud import vision

# 1. 输入：图片路径
image_path = r"C:\Users\gateman\Pictures\ocr_test\gemini_introduction.png"

# 2. 预处理：使用 Google Cloud Vision API 提取图片中的文本
def extract_text_from_image(path):
    client = vision.ImageAnnotatorClient()
    with open(path, "rb") as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        return texts[0].description
    else:
        return "No text detected."

extracted_text = extract_text_from_image(image_path)
logger.info(f"Extracted text: {extracted_text}")

# 3. 提示模板
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant that translates English to Chinese."),
        ("user", "Translate this sentence from English to Chinese. {text}"),
    ]
)

# 4. 模型调用
llm = ChatOpenAI(
    model="gemini-2.0-flash",
    temperature=0.2,  # 调整 temperature 以获得更稳定的翻译
    max_tokens=1000,
    api_key=src.configs.config.yaml_configs["gemini"]["api_key"],
)

# 5. 输出解析
output_parser = StrOutputParser()

# 构建链
chain = prompt | llm | output_parser

# 6. 执行链
if extracted_text != "No text detected.":
    output = chain.invoke({"text": extracted_text})
    logger.info(f"Translated text: {output}")
else:
    logger.info("No text to translate.")

# 7. 输出：翻译后的文本或错误信息 (已在执行链中通过 logger 输出)

logger.info("done!")