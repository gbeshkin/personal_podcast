from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from personal_podcast.pipeline import generate_episode

app = FastAPI(title="Personal Podcast", version="0.1.0")
app.mount("/files/episodes", StaticFiles(directory="episodes"), name="episode_files")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/episodes/generate")
def generate_daily_episode() -> dict[str, str]:
    files = generate_episode(
        config_path=Path("config/user.example.yaml"),
        output_dir=Path("episodes"),
    )
    audio_url = f"/files/episodes/{files.audio_path.name}" if files.audio_path else ""
    return {
        "script_path": str(files.script_path),
        "audio_path": str(files.audio_path) if files.audio_path else "",
        "audio_url": audio_url,
        "tts_status": files.tts_status,
    }
