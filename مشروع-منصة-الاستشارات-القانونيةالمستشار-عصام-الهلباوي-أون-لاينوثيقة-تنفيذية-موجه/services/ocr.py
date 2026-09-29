from pathlib import Path
import subprocess


class OCRService:
    """خدمة OCR اختيارية للمشروع الناتج."""

    def extract_text(self, image_path, language="eng"):
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"ملف الصورة غير موجود: {image_path}")

        try:
            result = subprocess.run(
                [
                    "tesseract",
                    str(image_path),
                    "stdout",
                    "-l",
                    str(language or "eng"),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("Tesseract OCR غير مثبت في بيئة التشغيل.") from exc
        except subprocess.CalledProcessError as exc:
            message = exc.stderr.strip() or "فشل استخراج النص من الصورة."
            raise RuntimeError(message) from exc

        return result.stdout.strip()


def extract_text(image_path, language="eng"):
    return OCRService().extract_text(image_path, language)
