from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from personal_podcast.models import AISettings, Section, Source, SourceType, TTSSettings, UserProfile


class ConfigError(ValueError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Config file does not exist: {path}")
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise ConfigError("Config root must be a mapping.")
    return data


def load_profile(data: dict[str, Any]) -> UserProfile:
    user = data.get("user", {})
    personalization = data.get("personalization", {})
    if not isinstance(user, dict):
        raise ConfigError("The 'user' section must be a mapping.")

    return UserProfile(
        name=str(user.get("name", "Григорий")),
        city=str(user.get("city", "Tallinn")),
        timezone=str(user.get("timezone", "Europe/Tallinn")),
        language=str(user.get("language", "ru")),
        target_duration_minutes=int(user.get("target_duration_minutes", 15)),
        favorite_topics=list(personalization.get("favorite_topics", [])),
        blocked_topics=list(personalization.get("blocked_topics", [])),
        companies=list(personalization.get("companies", [])),
        countries=list(personalization.get("countries", [])),
    )


def load_sections(data: dict[str, Any]) -> list[Section]:
    section_names = data.get("episode", {}).get(
        "include_sections",
        ["weather", "city_news", "world_news", "telegram", "youtube"],
    )
    return [Section(name) for name in section_names]


def _read_sources(data: dict[str, Any], key: str, source_type: SourceType) -> list[Source]:
    raw_sources = data.get("sources", {}).get(key, [])
    if not isinstance(raw_sources, list):
        return []

    sources: list[Source] = []
    for raw in raw_sources:
        if not isinstance(raw, dict):
            continue
        sources.append(
            Source(
                name=str(raw.get("name", "Unnamed source")),
                type=source_type,
                url=str(raw.get("url", "")),
                priority=int(raw.get("priority", 1)),
                external_id=str(raw.get("id")) if raw.get("id") is not None else None,
            )
        )
    return sources


def load_sources(data: dict[str, Any]) -> dict[Section, list[Source]]:
    return {
        Section.CITY_NEWS: _read_sources(data, "city_news", SourceType.RSS),
        Section.WORLD_NEWS: _read_sources(data, "world_news", SourceType.RSS),
        Section.TELEGRAM: _read_sources(data, "telegram_channels", SourceType.TELEGRAM_PUBLIC),
        Section.YOUTUBE: _read_sources(data, "youtube_channels", SourceType.YOUTUBE),
    }


def load_tts_settings(data: dict[str, Any]) -> TTSSettings:
    raw = data.get("tts", {})
    if not isinstance(raw, dict):
        return TTSSettings()

    return TTSSettings(
        provider=str(raw.get("provider", "openai")),
        model=str(raw.get("model", "tts-1-hd")),
        voice=str(raw.get("voice", "nova")),
        response_format=str(raw.get("format", "mp3")),
        speed=float(raw.get("speed", 0.95)),
        instructions=str(raw.get("instructions", TTSSettings.instructions)),
    )


def load_ai_settings(data: dict[str, Any]) -> AISettings:
    raw = data.get("ai", {})
    if not isinstance(raw, dict):
        return AISettings()

    return AISettings(
        provider=str(raw.get("provider", "openai")),
        translation_model=str(raw.get("translation_model", raw.get("script_model", "gpt-4o"))),
        enabled=bool(raw.get("enabled", True)),
    )
