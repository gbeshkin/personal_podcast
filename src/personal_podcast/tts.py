from __future__ import annotations

import inspect
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from dotenv import load_dotenv
from openai import OpenAI

from personal_podcast.models import TTSSettings

MAX_TTS_INPUT_CHARS = 3800


def synthesize_openai_speech(text: str, output_path: Path, settings: TTSSettings) -> str:
    if settings.provider != "openai":
        return f"skipped_unsupported_tts_provider:{settings.provider}"

    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        return "missing_openai_api_key"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    client = OpenAI()
    supports_instructions = "instructions" in inspect.signature(client.audio.speech.create).parameters
    chunks = split_tts_text(text)

    if len(chunks) == 1:
        _synthesize_chunk(client, chunks[0], output_path, settings, supports_instructions)
        return "generated" if supports_instructions else "generated_without_voice_instructions"

    with TemporaryDirectory() as temp_dir:
        part_paths: list[Path] = []
        for index, chunk in enumerate(chunks, start=1):
            part_path = Path(temp_dir) / f"part-{index:03d}.{settings.response_format}"
            _synthesize_chunk(client, chunk, part_path, settings, supports_instructions)
            part_paths.append(part_path)
        _join_audio_parts(part_paths, output_path)

    suffix = "" if supports_instructions else "_without_voice_instructions"
    return f"generated_chunked{suffix}:{len(chunks)}"


def split_tts_text(text: str, max_chars: int = MAX_TTS_INPUT_CHARS) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            for sentence_chunk in _split_long_paragraph(paragraph, max_chars):
                current = _append_or_flush(chunks, current, sentence_chunk, max_chars)
            continue
        current = _append_or_flush(chunks, current, paragraph, max_chars)

    if current:
        chunks.append(current)
    return chunks or [text[:max_chars]]


def _append_or_flush(chunks: list[str], current: str, addition: str, max_chars: int) -> str:
    candidate = f"{current}\n\n{addition}".strip() if current else addition
    if len(candidate) <= max_chars:
        return candidate
    if current:
        chunks.append(current)
    return addition


def _split_long_paragraph(paragraph: str, max_chars: int) -> list[str]:
    sentences = [part.strip() for part in paragraph.replace(". ", ".\n").splitlines() if part.strip()]
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(sentence[index : index + max_chars] for index in range(0, len(sentence), max_chars))
            continue
        current = _append_or_flush(chunks, current, sentence, max_chars)
    if current:
        chunks.append(current)
    return chunks


def _synthesize_chunk(
    client: OpenAI,
    text: str,
    output_path: Path,
    settings: TTSSettings,
    supports_instructions: bool,
) -> None:
    speech_kwargs = {
        "model": settings.model,
        "voice": settings.voice,
        "input": text.strip(),
        "response_format": settings.response_format,
    }
    if not settings.model.startswith("gpt-4o"):
        speech_kwargs["speed"] = settings.speed
    if supports_instructions:
        speech_kwargs["instructions"] = settings.instructions
    elif settings.model.startswith("gpt-4o"):
        speech_kwargs["extra_body"] = {"instructions": settings.instructions}

    with client.audio.speech.with_streaming_response.create(**speech_kwargs) as response:
        response.stream_to_file(output_path)


def _join_audio_parts(part_paths: list[Path], output_path: Path) -> None:
    with output_path.open("wb") as output_file:
        for part_path in part_paths:
            output_file.write(part_path.read_bytes())
