from personal_podcast.tts import MAX_TTS_INPUT_CHARS, split_tts_text


def test_split_tts_text_keeps_chunks_under_limit() -> None:
    text = "\n\n".join([f"Абзац номер {index}. " + ("Текст. " * 120) for index in range(10)])

    chunks = split_tts_text(text)

    assert len(chunks) > 1
    assert all(len(chunk) <= MAX_TTS_INPUT_CHARS for chunk in chunks)
