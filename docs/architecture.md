# Architecture

## Компоненты

### Scheduler

Запускает генерацию выпуска по расписанию. На старте можно использовать cron или
локальный CLI-запуск.

### Collectors

Модули, которые получают данные из источников:

- weather collector;
- RSS/news collector;
- Telegram public channel collector;
- YouTube collector.

### Normalizer

Приводит разные источники к единому формату `ContentItem`.

### Ranker

Выбирает самые важные и свежие материалы, убирает повторы и группирует похожие
темы.

### Script Generator

Создает текст выпуска. На вход получает профиль пользователя, погоду и список
материалов. На выходе дает структурированный сценарий.

### TTS

Озвучивает сценарий и возвращает аудиофайл.

### Audio Assembler

Собирает финальный файл: вступление, секции, паузы, завершение.

### Delivery

Доставляет выпуск пользователю. Для MVP: сохранить файл в `episodes/` и отправить
в Telegram.

## Поток данных

```text
UserProfile + Sources
  -> Collectors
  -> ContentItem[]
  -> Ranking and deduplication
  -> EpisodeScript
  -> TTS chunks
  -> EpisodeAudio
  -> Local file / delivery channel
```

## Риски

- Telegram и YouTube могут ограничивать доступ к данным.
- Новостные источники меняют RSS/API и формат страниц.
- Нужно аккуратно отделять факты от пересказа модели.
- Для новостей нужна свежесть, поэтому источники и API должны проверяться на
  актуальность.
- 15 минут аудио требует контроля длины текста.

## Технический старт

Предлагаемый стек для MVP:

- Python 3.12 для CLI и пайплайна.
- FastAPI для ручного запуска и будущего API.
- YAML для пользовательского конфига.
- `feedparser` для RSS.
- HTTP-клиент для weather API и внешних источников.
- Отдельный адаптер для TTS, чтобы позже легко менять провайдера.
- APScheduler или cron для запуска в 07:00.
- Railway для деплоя.

## Интерфейс CLI

```bash
personal-podcast generate --config config/user.yaml
```

Ожидаемый результат:

```text
episodes/2026-06-03-morning.mp3
episodes/2026-06-03-morning.md
```
