from datetime import date

from personal_podcast.models import ContentItem, Section, UserProfile, WeatherBrief
from personal_podcast.script_generator import generate_script


def test_generate_script_contains_core_sections() -> None:
    profile = UserProfile(
        name="Григорий",
        city="Tallinn",
        timezone="Europe/Tallinn",
        language="ru",
        target_duration_minutes=15,
    )
    weather = WeatherBrief(
        city="Tallinn",
        current_temp_c=18,
        feels_like_c=17,
        precipitation="дождь",
        wind="слабый",
        forecast="пасмурно",
        recommendation="возьмите зонт",
    )

    script = generate_script(
        profile=profile,
        episode_date=date(2026, 6, 3),
        sections=[Section.WEATHER, Section.CITY_NEWS, Section.WORLD_NEWS],
        weather=weather,
        city_news=[
            ContentItem(
                title="В городе открылась новая выставка",
                summary="Организаторы говорят, что программа рассчитана на всю неделю.",
                source_name="Test",
                source_url="https://example.com",
                published_at=None,
                category="city_news",
            )
        ],
        world_news=[],
        telegram_digest=[],
        youtube_digest=[],
    )

    assert "Доброе утро, Григорий. Это ваш утренний эфир." in script.markdown
    assert "Сегодня среда, 3 июня." in script.markdown
    assert "примерно на 15 минут" not in script.markdown
    assert "Начнем с погоды." in script.markdown
    assert "В городе Таллинне сейчас 18 градусов" in script.markdown
    assert "Теперь посмотрим, что заметно обсуждают в Таллинне." in script.markdown
    assert "Во-первых: В городе открылась новая выставка." in script.markdown
    assert "Источник:" not in script.markdown
    assert "## Погода" not in script.markdown
    assert "QA Lead Mode" not in script.markdown


def test_generate_script_supports_estonian_frame() -> None:
    profile = UserProfile(
        name="Grigori",
        city="Tallinn",
        timezone="Europe/Tallinn",
        language="et",
        target_duration_minutes=15,
    )
    weather = WeatherBrief(
        city="Tallinn",
        current_temp_c=18,
        feels_like_c=17,
        precipitation="без существенных осадков",
        wind="умеренный",
        forecast="днем переменная облачность, вечером прохладнее",
        recommendation="возьмите легкую куртку, зонт сегодня не обязателен",
    )

    script = generate_script(
        profile=profile,
        episode_date=date(2026, 6, 3),
        sections=[Section.WEATHER, Section.CITY_NEWS, Section.WORLD_NEWS],
        weather=weather,
        city_news=[],
        world_news=[],
        telegram_digest=[],
        youtube_digest=[],
    )

    assert "Tere hommikust, Grigori." in script.markdown
    assert "Täna on kolmapäev, 3. juuni." in script.markdown
    assert "Linnas Tallinn on praegu 18 kraadi" in script.markdown
    assert "Nüüd sellest, millest Tallinn täna räägitakse." in script.markdown
