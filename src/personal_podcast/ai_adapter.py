from __future__ import annotations

import json
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

from personal_podcast.models import AISettings, ContentItem


LANGUAGE_NAMES = {
    "ru": "русский",
    "russian": "русский",
    "et": "эстонский",
    "estonian": "эстонский",
    "en": "английский",
    "english": "английский",
}


def localize_items_for_episode(
    items: list[ContentItem],
    target_language: str,
    settings: AISettings,
) -> list[ContentItem]:
    if not items or not settings.enabled or settings.provider != "openai":
        return items

    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        return items

    localized: list[ContentItem] = []
    client = OpenAI()
    for item in items:
        if _looks_like_language(item.title + " " + item.summary, target_language):
            localized.append(item)
            continue
        localized.append(_localize_item(client, item, target_language, settings))
    return localized


def _localize_item(
    client: OpenAI,
    item: ContentItem,
    target_language: str,
    settings: AISettings,
) -> ContentItem:
    language_name = LANGUAGE_NAMES.get(target_language.lower(), target_language)
    prompt = {
        "title": item.title,
        "summary": item.summary,
    }
    try:
        response = client.chat.completions.create(
            model=settings.translation_model,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Переведи и адаптируй новость на {language_name} для утреннего "
                        "радиоэфира. Не добавляй фактов. Сохрани имена, компании и числа. "
                        "Верни только JSON с полями title и summary. Summary сделай одной "
                        "естественной фразой до 280 символов."
                    ),
                },
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
        )
    except Exception:
        return item

    content = response.choices[0].message.content or ""
    parsed = _parse_json_object(content)
    title = str(parsed.get("title", item.title)).strip() if parsed else item.title
    summary = str(parsed.get("summary", item.summary)).strip() if parsed else item.summary
    return ContentItem(
        title=title,
        summary=summary,
        source_name=item.source_name,
        source_url=item.source_url,
        published_at=item.published_at,
        category=item.category,
        priority=item.priority,
    )


def _looks_like_language(text: str, target_language: str) -> bool:
    if target_language.lower() in {"ru", "russian"}:
        return _cyrillic_ratio(text) > 0.25
    if target_language.lower() in {"en", "english"}:
        return _latin_ratio(text) > 0.6
    return False


def _cyrillic_ratio(text: str) -> float:
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return 0
    cyrillic = [char for char in letters if "а" <= char.lower() <= "я" or char.lower() == "ё"]
    return len(cyrillic) / len(letters)


def _latin_ratio(text: str) -> float:
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return 0
    latin = [char for char in letters if "a" <= char.lower() <= "z"]
    return len(latin) / len(letters)


def _parse_json_object(content: str) -> dict[str, object]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if not match:
            return {}
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}
    return parsed if isinstance(parsed, dict) else {}
