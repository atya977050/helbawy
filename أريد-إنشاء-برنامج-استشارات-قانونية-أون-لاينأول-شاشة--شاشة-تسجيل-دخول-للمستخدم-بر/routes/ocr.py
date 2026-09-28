from pathlib import Path

from services.ocr import OCRService


def extract_uploaded_image(image_path, language="eng"):
    return OCRService().extract_text(
        Path(image_path),
        language,
    )
