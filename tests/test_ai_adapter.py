from personal_podcast.ai_adapter import _looks_like_language


def test_looks_like_russian_for_cyrillic_text() -> None:
    assert _looks_like_language("Доброе утро, главные новости города", "ru")


def test_looks_like_russian_rejects_english_text() -> None:
    assert not _looks_like_language("Iran targets neighbors as U.S. condemns strikes", "ru")
