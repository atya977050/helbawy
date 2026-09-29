from pathlib import Path
import subprocess


class VoiceService:
    """خدمة الصوت الاختيارية للمشروع الناتج."""

    def transcribe(self, audio_path, language="ar"):
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise FileNotFoundError(
                f"ملف الصوت غير موجود: {audio_path}"
            )

        raise RuntimeError(
            "محرك تحويل الصوت إلى نص غير موصل بعد. "
            "الخدمة جاهزة للربط بمحرك STT."
        )

    def synthesize(self, text, language="ar", output_path=None):
        text = str(text or "").strip()

        if not text:
            raise ValueError("النص المطلوب تحويله إلى صوت فارغ.")

        raise RuntimeError(
            "محرك تحويل النص إلى صوت غير موصل بعد. "
            "الخدمة جاهزة للربط بمحرك TTS."
        )


def transcribe(audio_path, language="ar"):
    return VoiceService().transcribe(audio_path, language)


def synthesize(text, language="ar", output_path=None):
    return VoiceService().synthesize(
        text,
        language,
        output_path,
    )
