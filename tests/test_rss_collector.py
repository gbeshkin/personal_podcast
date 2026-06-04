from datetime import UTC, datetime
from xml.etree import ElementTree

from personal_podcast.collectors import _parse_rss
from personal_podcast.models import Source, SourceType


def test_parse_rss_items() -> None:
    root = ElementTree.fromstring(
        """
        <rss version="2.0">
          <channel>
            <item>
              <title>Новость дня</title>
              <link>https://example.com/news</link>
              <description><![CDATA[Короткое <b>описание</b> новости.]]></description>
              <pubDate>Wed, 03 Jun 2026 07:00:00 GMT</pubDate>
            </item>
          </channel>
        </rss>
        """
    )
    source = Source(
        name="Example RSS",
        type=SourceType.RSS,
        url="https://example.com/rss",
    )

    items = _parse_rss(root, source, "world_news", 5)

    assert len(items) == 1
    assert items[0].title == "Новость дня"
    assert items[0].summary == "Короткое описание новости."
    assert items[0].source_url == "https://example.com/news"
    assert items[0].published_at == datetime(2026, 6, 3, 7, 0, tzinfo=UTC)
