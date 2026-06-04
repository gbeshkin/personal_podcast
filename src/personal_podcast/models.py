from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from pathlib import Path


class Section(StrEnum):
    WEATHER = "weather"
    CITY_NEWS = "city_news"
    WORLD_NEWS = "world_news"
    TELEGRAM = "telegram"
    YOUTUBE = "youtube"


class SourceType(StrEnum):
    RSS = "rss"
    TELEGRAM_PUBLIC = "telegram_public"
    YOUTUBE = "youtube"
    MUNICIPAL = "municipal"


@dataclass(frozen=True)
class UserProfile:
    name: str
    city: str
    timezone: str
    language: str
    target_duration_minutes: int
    favorite_topics: list[str] = field(default_factory=list)
    blocked_topics: list[str] = field(default_factory=list)
    companies: list[str] = field(default_factory=list)
    countries: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Source:
    name: str
    type: SourceType
    url: str
    priority: int = 1
    external_id: str | None = None


@dataclass(frozen=True)
class WeatherBrief:
    city: str
    current_temp_c: float
    feels_like_c: float
    precipitation: str
    wind: str
    forecast: str
    recommendation: str


@dataclass(frozen=True)
class ContentItem:
    title: str
    summary: str
    source_name: str
    source_url: str
    published_at: datetime | None
    category: str
    priority: int = 1


@dataclass(frozen=True)
class EpisodeRequest:
    profile: UserProfile
    episode_date: date
    sections: list[Section]
    smart_briefing_minutes: int | None = None


@dataclass(frozen=True)
class EpisodeScript:
    title: str
    episode_date: date
    language: str
    estimated_duration_minutes: int
    markdown: str
    narration_text: str


@dataclass(frozen=True)
class AISettings:
    provider: str = "openai"
    translation_model: str = "gpt-4o"
    enabled: bool = True


@dataclass(frozen=True)
class TTSSettings:
    provider: str = "openai"
    model: str = "tts-1-hd"
    voice: str = "nova"
    response_format: str = "mp3"
    speed: float = 0.95
    instructions: str = (
        "Говори по-русски как живой ведущий утреннего радио-шоу: тепло, естественно, "
        "с легкой улыбкой в голосе и спокойными паузами между темами."
    )


@dataclass(frozen=True)
class EpisodeFiles:
    script_path: Path
    audio_path: Path | None
    tts_status: str
