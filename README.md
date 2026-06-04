# Персональный подкаст

Система, которая каждое утро собирает персональный 15-минутный аудиовыпуск:
погода в выбранном городе, свежие городские и мировые новости, открытые каналы
из Telegram и YouTube, затем краткий сценарий и озвучка в один файл для завтрака,
прогулки или пробежки.

## Идея

Вместо того чтобы утром листать несколько источников, пользователь получает один
короткий выпуск с тем, что важно именно ему. Формат должен быть похож на личного
ведущего: спокойно, структурно, без лишнего шума и с понятными переходами между
темами.

## MVP

Первый рабочий прототип должен уметь:

1. Читать конфиг пользователя: город, язык, длительность, список источников.
2. Получать погоду на сегодня.
3. Собирать новости из нескольких RSS/API-источников.
4. Читать открытые источники: Telegram-каналы и YouTube-каналы/видео, где это
   доступно легально и технически устойчиво.
5. Делать краткую выжимку и сценарий выпуска.
6. Озвучивать сценарий через TTS.
7. Сохранять готовый аудиофайл локально и в архиве.
8. Отправлять выпуск в Telegram.
9. Запускаться по расписанию каждое утро в 07:00.

## Предлагаемый пайплайн

```text
Scheduler
  -> Source collectors
  -> Normalization
  -> Relevance ranking
  -> Script generation
  -> Text-to-speech
  -> Audio assembly
  -> Delivery
```

## Источники данных

- Погода: weather API.
- Городские новости: RSS, локальные медиа, официальные городские источники.
- Мировые новости: RSS/API надежных медиа.
- Telegram: только публичные каналы и только через допустимые способы доступа.
- YouTube: каналы, RSS-фиды, метаданные и транскрипты, когда они доступны.

## Базовые сущности

- `UserProfile`: город, язык, часовой пояс, длительность выпуска.
- `Source`: тип источника, URL/ID, приоритет, правила фильтрации.
- `ContentItem`: нормализованная новость, пост или видео.
- `EpisodeScript`: готовый текст выпуска с секциями и таймингами.
- `EpisodeAudio`: итоговый аудиофайл и метаданные.

## Открытые решения

- Какой TTS использовать: OpenAI, ElevenLabs, локальный движок или другое.
- Где хранить настройки: YAML на старте, позже PostgreSQL.
- Как хранить аудио: локально на старте, позже S3-compatible storage.
- Нужен ли веб-интерфейс или достаточно CLI на первом этапе.
- Какой город и какие источники берем для первого тестового выпуска.

## Первый прототип

Наиболее быстрый путь:

1. CLI-команда `personal-podcast generate`.
2. Конфиг в `config/user.example.yaml`.
3. Погода + 2-3 RSS-источника.
4. Генерация сценария в Markdown.
5. FastAPI endpoint для ручного запуска.
6. Озвучка в MP3.
7. Локальное сохранение в `episodes/`.
8. Telegram-доставка.

## Локальный запуск

```bash
PYTHONPATH=src python3 -m uvicorn personal_podcast.app:app --host 127.0.0.1 --port 8000
```

Ручная генерация выпуска:

```bash
PYTHONPATH=src python3 -m personal_podcast.cli generate --config config/user.example.yaml --output-dir episodes
```

## OpenAI TTS

Для генерации MP3 нужен ключ OpenAI:

```bash
export OPENAI_API_KEY=sk-your-api-key
```

После этого `personal-podcast generate` и `POST /episodes/generate` будут создавать
не только Markdown-сценарий, но и MP3-файл в `episodes/`.

## Технологии

- Backend: Python 3.12, FastAPI.
- AI: OpenAI-compatible LLM provider.
- Speech: OpenAI TTS или ElevenLabs.
- Scheduler: APScheduler или cron.
- Storage: PostgreSQL и S3-compatible storage после MVP.
- Deployment: Railway.

## Структура проекта

```text
personal_podcast/
  config/
    user.example.yaml
  docs/
    product_brief.md
    architecture.md
  episodes/
    .gitkeep
  src/
    personal_podcast/
      __init__.py
      app.py
      cli.py
      collectors.py
      config.py
      models.py
      pipeline.py
      script_generator.py
  tests/
  README.md
```
