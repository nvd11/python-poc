from src.services.google_ocr_service import google_ocr_service
import src.configs.config
from loguru import logger

def test_generate_text():
    logger.info("test_generate_text")
    image_path = r"C:\Users\gateman\Pictures\ocr_test\gemini_introduction.png"
    text = google_ocr_service.extract_text_from_img(image_path)
    logger.info(text)
    assert text is not None