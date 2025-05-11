from services.google_ocr_service import GoogleOCRService
import src.configs.config
from loguru import logger


# get text data from an image
image_path = r"C:\Users\gateman\Pictures\ocr_test\gemini_introduction.png"
words_text = GoogleOCRService.extract_text_from_img(image_path)


