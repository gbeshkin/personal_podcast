from __future__ import annotations

from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from html import unescape
import os
import re
from xml.etree import ElementTree

from dotenv import load_dotenv
import httpx

from personal_podcast.models import ContentItem, Source, WeatherBrief

RSS_TIMEOUT_SECONDS = 15
RSS_USER_AGENT = "personal-podcast/0.1 (+https://localhost)"


def collect_weather(city: str) -> WeatherBrief:
    return WeatherBrief(
        city=city,
        current_temp_c=18,
        feels_like_c=17,
        precipitation="без существенных осадков",
        wind="умеренный",
        forecast="днем переменная облачность, вечером прохладнее",
        recommendation="возьмите легкую куртку, зонт сегодня не обязателен",
    )


def collect_placeholder_items(sources: list[Source], category: str) -> list[ContentItem]:
    items: list[ContentItem] = []
    for source in sources:
        if not source.url and not source.external_id:
            continue
        source_reference = source.url or f"id:{source.external_id}"
        items.append(
            ContentItem(
                title=f"Новый материал из {source.name}",
                summary=(
                    "Здесь будет AI-сводка после подключения реального коллектора "
                    "и LLM-обработки."
                ),
                source_name=source.name,
                source_url=source_reference,
                published_at=datetime.now(UTC),
                category=category,
                priority=source.priority,
            )
        )
    return sorted(items, key=lambda item: item.priority)


def collect_telegram_items(sources: list[Source], limit_per_source: int = 5) -> list[ContentItem]:
    load_dotenv()
    if not sources:
        return []

    if not os.getenv("TELEGRAM_API_ID") or not os.getenv("TELEGRAM_API_HASH"):
        return [
            ContentItem(
                title="Telegram-канал добавлен, но доступ еще не настроен",
                summary=(
                    "Чтобы читать последние сообщения, нужны TELEGRAM_API_ID и "
                    "TELEGRAM_API_HASH. После этого collector сможет получить посты канала."
                ),
                source_name=", ".join(source.name for source in sources),
                source_url=", ".join(source.url or f"id:{source.external_id}" for source in sources),
                published_at=datetime.now(UTC),
                category="telegram",
                priority=10,
            )
        ]

    try:
        return _collect_telegram_items_with_telethon(sources, limit_per_source)
    except Exception as error:
        return [
            ContentItem(
                title="Telegram collector пока не смог прочитать канал",
                summary=str(error),
                source_name=", ".join(source.name for source in sources),
                source_url=", ".join(source.url or f"id:{source.external_id}" for source in sources),
                published_at=datetime.now(UTC),
                category="telegram",
                priority=10,
            )
        ]


def _collect_telegram_items_with_telethon(
    sources: list[Source],
    limit_per_source: int,
) -> list[ContentItem]:
    try:
        from telethon.sync import TelegramClient
    except ImportError as error:
        raise RuntimeError("Установите зависимость telethon: pip install telethon") from error

    api_id = int(os.environ["TELEGRAM_API_ID"])
    api_hash = os.environ["TELEGRAM_API_HASH"]
    session_name = os.getenv("TELEGRAM_SESSION", "personal_podcast")
    items: list[ContentItem] = []
    with TelegramClient(session_name, api_id, api_hash) as client:
        for source in sources:
            entity_ref: int | str
            if source.external_id:
                raw_id = str(source.external_id)
                entity_ref = int(raw_id) if raw_id.isdigit() else raw_id
            else:
                entity_ref = source.url
            for message in client.iter_messages(entity_ref, limit=limit_per_source):
                text = (message.message or "").strip()
                if not text:
                    continue
                items.append(
                    ContentItem(
                        title=_clean_summary(text, max_length=120),
                        summary=_clean_summary(text, max_length=360),
                        source_name=source.name,
                        source_url=source.url or f"id:{source.external_id}",
                        published_at=message.date.astimezone(UTC) if message.date else None,
                        category="telegram",
                        priority=source.priority,
                    )
                )
    return sorted(
        items,
        key=lambda item: (item.published_at or datetime.min.replace(tzinfo=UTC), item.priority),
        reverse=True,
    )


def collect_rss_items(sources: list[Source], category: str, limit_per_source: int = 5) -> list[ContentItem]:
    items: list[ContentItem] = []
    for source in sources:
        if not source.url:
            continue
        try:
            items.extend(_fetch_rss_source(source, category, limit_per_source))
        except (httpx.HTTPError, ElementTree.ParseError, UnicodeDecodeError):
            continue
    return sorted(
        items,
        key=lambda item: (item.published_at or datetime.min.replace(tzinfo=UTC), item.priority),
        reverse=True,
    )


def _fetch_rss_source(source: Source, category: str, limit: int) -> list[ContentItem]:
    response = httpx.get(
        source.url,
        follow_redirects=True,
        timeout=RSS_TIMEOUT_SECONDS,
        headers={"User-Agent": RSS_USER_AGENT},
    )
    response.raise_for_status()
    root = ElementTree.fromstring(response.content)

    if root.tag.endswith("feed"):
        return _parse_atom(root, source, category, limit)
    return _parse_rss(root, source, category, limit)


def _parse_rss(root: ElementTree.Element, source: Source, category: str, limit: int) -> list[ContentItem]:
    items: list[ContentItem] = []
    for node in root.findall("./channel/item")[:limit]:
        title = _node_text(node, "title")
        link = _node_text(node, "link") or source.url
        summary = _clean_summary(_node_text(node, "description"))
        published_at = _parse_datetime(_node_text(node, "pubDate"))
        if not title:
            continue
        items.append(
            ContentItem(
                title=title,
                summary=summary,
                source_name=source.name,
                source_url=link,
                published_at=published_at,
                category=category,
                priority=source.priority,
            )
        )
    return items


def _parse_atom(root: ElementTree.Element, source: Source, category: str, limit: int) -> list[ContentItem]:
    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("atom:entry", namespace) or root.findall("entry")
    items: list[ContentItem] = []
    for node in entries[:limit]:
        title = _node_text(node, "title") or _node_text(node, "atom:title", namespace)
        link = _atom_link(node, namespace) or source.url
        summary = _clean_summary(
            _node_text(node, "summary") or _node_text(node, "atom:summary", namespace)
        )
        published_at = _parse_datetime(
            _node_text(node, "updated") or _node_text(node, "atom:updated", namespace)
        )
        if not title:
            continue
        items.append(
            ContentItem(
                title=title,
                summary=summary,
                source_name=source.name,
                source_url=link,
                published_at=published_at,
                category=category,
                priority=source.priority,
            )
        )
    return items


def _node_text(
    node: ElementTree.Element,
    path: str,
    namespace: dict[str, str] | None = None,
) -> str:
    child = node.find(path, namespace or {})
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def _atom_link(node: ElementTree.Element, namespace: dict[str, str]) -> str:
    links = node.findall("atom:link", namespace) or node.findall("link")
    for link in links:
        href = link.attrib.get("href")
        if href:
            return href
    return ""


def _clean_summary(value: str, max_length: int = 360) -> str:
    text = unescape(re.sub(r"<[^>]+>", " ", value or ""))
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_length:
        return text
    return text[: max_length - 1].rstrip() + "..."


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError, AttributeError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
