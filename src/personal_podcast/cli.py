from __future__ import annotations

import argparse
from pathlib import Path

from personal_podcast.pipeline import generate_episode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="personal-podcast")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="Generate a daily podcast script.")
    generate.add_argument("--config", type=Path, default=Path("config/user.example.yaml"))
    generate.add_argument("--output-dir", type=Path, default=Path("episodes"))
    generate.add_argument("--skip-tts", action="store_true", help="Generate only the script.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "generate":
        files = generate_episode(
            config_path=args.config,
            output_dir=args.output_dir,
            synthesize_audio=not args.skip_tts,
        )
        print(f"Generated episode script: {files.script_path}")
        print(f"TTS status: {files.tts_status}")
        if files.audio_path:
            print(f"Generated episode audio: {files.audio_path}")


if __name__ == "__main__":
    main()
