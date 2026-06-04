from __future__ import annotations

from datetime import date

from personal_podcast.models import ContentItem, EpisodeScript, Section, UserProfile, WeatherBrief

LOCALIZED_CITY_NAMES = {
    "ru": {
        "Tallinn": {"default": "Таллинн", "prepositional": "Таллинне"},
        "Таллинн": {"default": "Таллинн", "prepositional": "Таллинне"},
        "Tartu": {"default": "Тарту", "prepositional": "Тарту"},
        "Narva": {"default": "Нарва", "prepositional": "Нарве"},
        "Riga": {"default": "Рига", "prepositional": "Риге"},
        "Vilnius": {"default": "Вильнюс", "prepositional": "Вильнюсе"},
    }
}

ET_WEEKDAYS = {
    0: "esmaspäev",
    1: "teisipäev",
    2: "kolmapäev",
    3: "neljapäev",
    4: "reede",
    5: "laupäev",
    6: "pühapäev",
}

ET_MONTHS = {
    1: "jaanuar",
    2: "veebruar",
    3: "märts",
    4: "aprill",
    5: "mai",
    6: "juuni",
    7: "juuli",
    8: "august",
    9: "september",
    10: "oktoober",
    11: "november",
    12: "detsember",
}

ET_WEATHER_PHRASES = {
    "без существенных осадков": "olulisi sademeid ei ole",
    "умеренный": "mõõdukas",
    "днем переменная облачность, вечером прохладнее": "päeval on vahelduv pilvisus, õhtul läheb jahedamaks",
    "возьмите легкую куртку, зонт сегодня не обязателен": "võta kerge jope kaasa, vihmavari ei ole täna hädavajalik",
}


RU_WEEKDAYS = {
    0: "понедельник",
    1: "вторник",
    2: "среда",
    3: "четверг",
    4: "пятница",
    5: "суббота",
    6: "воскресенье",
}

RU_MONTHS = {
    1: "января",
    2: "февраля",
    3: "марта",
    4: "апреля",
    5: "мая",
    6: "июня",
    7: "июля",
    8: "августа",
    9: "сентября",
    10: "октября",
    11: "ноября",
    12: "декабря",
}


def format_ru_date(value: date) -> str:
    return f"{RU_WEEKDAYS[value.weekday()]}, {value.day} {RU_MONTHS[value.month]}"


def format_episode_date(value: date, language: str) -> str:
    if language.lower() in {"et", "estonian"}:
        return f"{ET_WEEKDAYS[value.weekday()]}, {value.day}. {ET_MONTHS[value.month]}"
    return format_ru_date(value)


def localize_place_name(value: str, language: str, grammatical_case: str = "default") -> str:
    localized = LOCALIZED_CITY_NAMES.get(language.lower(), {}).get(value)
    if isinstance(localized, dict):
        return localized.get(grammatical_case, localized["default"])
    return value


def render_story_brief(
    items: list[ContentItem],
    empty_text: str,
    limit: int = 3,
    language: str = "ru",
) -> str:
    if not items:
        return empty_text

    story_parts = []
    transitions = (
        ["Kõigepealt", "Veel üks oluline teema", "Ja lühidalt veel ühest asjast"]
        if language.lower() in {"et", "estonian"}
        else ["Во-первых", "Еще одна важная тема", "И коротко еще об одном"]
    )
    for index, item in enumerate(items[:limit]):
        title = _clean_for_radio(item.title)
        summary = _clean_for_radio(item.summary)
        transition = transitions[index] if index < len(transitions) else "Также"
        if summary:
            story_parts.append(f"{transition}: {title}. {summary}.")
        else:
            story_parts.append(f"{transition}: {title}.")
    return " ".join(story_parts)


def _clean_for_radio(value: str) -> str:
    cleaned = " ".join((value or "").replace("\n", " ").split())
    return cleaned.rstrip(".")


def _localize_weather_phrase(value: str, language: str) -> str:
    if language.lower() in {"et", "estonian"}:
        return ET_WEATHER_PHRASES.get(value, value)
    return value


def generate_script(
    profile: UserProfile,
    episode_date: date,
    sections: list[Section],
    weather: WeatherBrief | None,
    city_news: list[ContentItem],
    world_news: list[ContentItem],
    telegram_digest: list[ContentItem],
    youtube_digest: list[ContentItem],
) -> EpisodeScript:
    target_duration = profile.target_duration_minutes
    is_estonian = profile.language.lower() in {"et", "estonian"}
    title = (
        f"Hommikune saade {episode_date.isoformat()}"
        if is_estonian
        else f"Утренний выпуск на {episode_date.isoformat()}"
    )
    today = format_episode_date(episode_date, profile.language)
    city_name = localize_place_name(profile.city, profile.language, "prepositional")
    if is_estonian:
        parts = [
            f"Tere hommikust, {profile.name}. See on sinu hommikune saade.",
            f"Täna on {today}. Alustame rahulikult: ilm, linn ja selle tunni olulisemad uudised.",
        ]
    else:
        parts = [
            f"Доброе утро, {profile.name}. Это ваш утренний эфир.",
            f"Сегодня {today}. Давайте спокойно начнем день: коротко про погоду, город и главные новости к этому часу.",
        ]

    if Section.WEATHER in sections and weather:
        precipitation = _localize_weather_phrase(weather.precipitation, profile.language)
        wind = _localize_weather_phrase(weather.wind, profile.language)
        forecast = _localize_weather_phrase(weather.forecast, profile.language)
        recommendation = _localize_weather_phrase(weather.recommendation, profile.language)
        if is_estonian:
            weather_text = (
                f"Alustame ilmast. Linnas {localize_place_name(weather.city, profile.language)} "
                f"on praegu {weather.current_temp_c:g} kraadi, tunnetuslikult umbes "
                f"{weather.feels_like_c:g}. Sademete poolest: {precipitation}. "
                f"Tuul on {wind}. Lähitundidel on oodata: {forecast}. "
                f"Hommikune praktiline soovitus: {recommendation}."
            )
        else:
            weather_text = (
                f"Начнем с погоды. В городе "
                f"{localize_place_name(weather.city, profile.language, 'prepositional')} сейчас "
                f"{weather.current_temp_c:g} градусов, "
                f"по ощущениям около {weather.feels_like_c:g}. "
                f"По осадкам: {precipitation}. Ветер {wind}. "
                f"В ближайшие часы ожидается: {forecast}. "
                f"Практический вывод на утро: {recommendation}."
            )
        parts.extend(
            [
                weather_text,
            ]
        )

    if Section.CITY_NEWS in sections:
        parts.extend(
            [
                (
                    f"Nüüd sellest, millest {city_name} täna räägitakse. "
                    if is_estonian
                    else f"Теперь посмотрим, что заметно обсуждают в {city_name}. "
                )
                + render_story_brief(
                    city_news,
                    (
                        "Värskeid linnauudiseid on ühendatud allikates praegu vähe, liigume rahulikult edasi."
                        if is_estonian
                        else "Пока свежих городских новостей из подключенных источников немного, так что без лишнего шума идем дальше."
                    ),
                    language=profile.language,
                ),
            ]
        )

    if Section.WORLD_NEWS in sections:
        parts.extend(
            [
                (
                    "Maailma päevakorras on praegu mitu teemat. "
                    if is_estonian
                    else "Теперь быстро посмотрим, что происходит в мире. "
                )
                + render_story_brief(
                    world_news,
                    (
                        "Värskeid maailmauudiseid on ühendatud allikates praegu vähe."
                        if is_estonian
                        else "Пока свежих мировых новостей из подключенных источников немного."
                    ),
                    language=profile.language,
                ),
            ]
        )

    if Section.TELEGRAM in sections:
        parts.extend(
            [
                (
                    "Valitud Telegrami kanalites, ilma pika kerimiseta: "
                    if is_estonian
                    else "В выбранных Telegram-каналах сегодня без длинной прокрутки: "
                )
                + render_story_brief(
                    telegram_digest,
                    (
                        "Valitud Telegrami kanalites ei ole praegu uusi materjale."
                        if is_estonian
                        else "В выбранных Telegram-каналах пока нет новых материалов."
                    ),
                    limit=2,
                    language=profile.language,
                ),
            ]
        )

    if Section.YOUTUBE in sections:
        parts.extend(
            [
                ("Ja lühidalt YouTube'ist. " if is_estonian else "И коротко о YouTube. ")
                + render_story_brief(
                    youtube_digest,
                    (
                        "Valitud YouTube'i kanalites ei ole praegu uusi videoid."
                        if is_estonian
                        else "На выбранных YouTube-каналах пока нет новых видео."
                    ),
                    limit=2,
                    language=profile.language,
                ),
            ]
        )

    parts.append(
        "Sellega on tänaseks kõik. Ilusat hommikut ja rahulikku päeva algust."
        if is_estonian
        else "На этом все. Хорошего вам утра и мягкого входа в день."
    )
    narration_text = "\n\n".join(parts) + "\n"
    markdown = f"# {title}\n\n{narration_text}"
    return EpisodeScript(
        title=title,
        episode_date=episode_date,
        language=profile.language,
        estimated_duration_minutes=target_duration,
        markdown=markdown,
        narration_text=narration_text,
    )
