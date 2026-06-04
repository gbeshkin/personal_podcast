from __future__ import annotations

from datetime import date
from pathlib import Path

from personal_podcast.ai_adapter import localize_items_for_episode
from personal_podcast.collectors import (
    collect_placeholder_items,
    collect_rss_items,
    collect_telegram_items,
    collect_weather,
)
from personal_podcast.config import (
    load_ai_settings,
    load_profile,
    load_sections,
    load_sources,
    load_tts_settings,
    load_yaml,
)
from personal_podcast.models import EpisodeFiles, Section
from personal_podcast.script_generator import generate_script
from personal_podcast.tts import synthesize_openai_speech


def generate_episode(
    config_path: Path,
    output_dir: Path,
    episode_date: date | None = None,
    synthesize_audio: bool = True,
) -> EpisodeFiles:
    data = load_yaml(config_path)
    profile = load_profile(data)
    sections = load_sections(data)
    sources = load_sources(data)
    ai_settings = load_ai_settings(data)
    tts_settings = load_tts_settings(data)
    current_date = episode_date or date.today()

    weather = collect_weather(profile.city) if Section.WEATHER in sections else None
    city_news = collect_rss_items(sources.get(Section.CITY_NEWS, []), "city_news")
    world_news = collect_rss_items(sources.get(Section.WORLD_NEWS, []), "world_news")
    telegram = collect_telegram_items(sources.get(Section.TELEGRAM, []))
    youtube = collect_placeholder_items(sources.get(Section.YOUTUBE, []), "youtube")

    city_news = localize_items_for_episode(city_news, profile.language, ai_settings)
    world_news = localize_items_for_episode(world_news, profile.language, ai_settings)
    telegram = localize_items_for_episode(telegram, profile.language, ai_settings)
    youtube = localize_items_for_episode(youtube, profile.language, ai_settings)

    script = generate_script(
        profile=profile,
        episode_date=current_date,
        sections=sections,
        weather=weather,
        city_news=city_news,
        world_news=world_news,
        telegram_digest=telegram,
        youtube_digest=youtube,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    language_suffix = "" if profile.language == "ru" else f"-{profile.language}"
    file_stem = f"{current_date.isoformat()}-morning{language_suffix}"
    script_path = output_dir / f"{file_stem}.md"
    audio_path = output_dir / f"{file_stem}.{tts_settings.response_format}"
    script_path.write_text(script.markdown, encoding="utf-8")
    tts_status = (
        synthesize_openai_speech(script.narration_text, audio_path, tts_settings)
        if synthesize_audio
        else "skipped"
    )
    return EpisodeFiles(
        script_path=script_path,
        audio_path=audio_path if tts_status.startswith("generated") else None,
        tts_status=tts_status,
    )
