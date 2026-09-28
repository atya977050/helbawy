from services.voice import VoiceService


def transcribe_audio(audio_path, language="ar"):
    return VoiceService().transcribe(
        audio_path,
        language,
    )


def synthesize_text(
    text,
    language="ar",
    output_path=None,
):
    return VoiceService().synthesize(
        text,
        language,
        output_path,
    )
