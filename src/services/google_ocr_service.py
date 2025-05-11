import src.configs.config
import os
from google.cloud import vision



class GoogleOCRService:

    def __init__(self):
        """
        Initializes the OCR service with the specified engine.
        Currently, it uses the Google Cloud Vision API as the OCR engine.
        Google credentail file is defined as a system variable GOOGLE_APPLICATION_CREDENTIALS.
        """
        self._client = vision.ImageAnnotatorClient()
        # check env variable
        if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
            raise Exception(
                "GOOGLE_APPLICATION_CREDENTIALS environment variable not set."
            )


    def extract_text_from_img(self, image_path):
        """
        Extracts text from a img file using the Google Cloud Vision API.

        Args:
            pdf_path (str): The path to the PDF file.
        
        """
        with open(image_path, "rb") as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        response = self._client.text_detection(image=image)
        if response.error.message:
            raise
        texts = response.text_annotations
        if texts:
            return texts[0].description
        else:
            raise Exception("No text detected.")
        
google_ocr_service = GoogleOCRService()


