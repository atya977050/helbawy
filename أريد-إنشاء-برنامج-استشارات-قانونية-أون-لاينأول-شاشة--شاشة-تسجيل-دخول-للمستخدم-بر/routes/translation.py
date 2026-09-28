from services.translation import TranslationService


def translate_text(
    source_text,
    source_language="auto",
    target_language="ar",
):
    return TranslationService().translate(
        source_text,
        source_language,
        target_language,
    )
