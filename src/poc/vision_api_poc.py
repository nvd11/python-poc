import src.configs.config

def detect_text(path):
    """Detects text in the file."""
    from google.cloud import vision

    client = vision.ImageAnnotatorClient()

    with open(path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    print("Texts:")

    if texts:
        # 获取完整的文本内容
        full_text = texts[0].description
        print("Texts:")
        print(full_text)
    else:
        print("No text detected.")
    
    
    print("----end----")

    if response.error.message:
        raise Exception(
            "{}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
        )

detect_text(r"C:\Users\gateman\Pictures\ocr_test\013845.png")

