from personal_podcast.collectors import collect_telegram_items
from personal_podcast.models import Source, SourceType


def test_collect_telegram_items_reports_missing_credentials(monkeypatch) -> None:
    monkeypatch.delenv("TELEGRAM_API_ID", raising=False)
    monkeypatch.delenv("TELEGRAM_API_HASH", raising=False)
    source = Source(
        name="Telegram channel 1001092413834",
        type=SourceType.TELEGRAM_PUBLIC,
        url="",
        external_id="1001092413834",
    )

    items = collect_telegram_items([source])

    assert len(items) == 1
    assert "доступ еще не настроен" in items[0].title
