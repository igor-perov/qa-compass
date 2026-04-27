#!/usr/bin/env python3

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / "skills"
DEFAULT_SKILLS = [
    "qa-compass",
    "confluence-qa-orchestrator",
    "requirements-qa-orchestrator",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install packaged skills from this repo into a local Codex skills directory."
    )
    parser.add_argument(
        "--dest",
        default=str(Path.home() / ".codex" / "skills"),
        help="Destination skills directory. Defaults to ~/.codex/skills",
    )
    parser.add_argument(
        "--skill",
        action="append",
        choices=DEFAULT_SKILLS,
        help="Skill to install. Repeat to install multiple skills. Defaults to all bundled skills.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing destination skill directory.",
    )
    return parser.parse_args()


def install_skill(skill_name: str, destination_root: Path, overwrite: bool) -> Path:
    source = SKILLS_ROOT / skill_name
    if not source.exists():
        raise FileNotFoundError(f"Bundled skill not found: {source}")

    destination = destination_root / skill_name
    if destination.exists():
        if not overwrite:
            raise FileExistsError(
                f"Destination already exists: {destination}. Re-run with --overwrite to replace it."
            )
        shutil.rmtree(destination)

    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
    )
    return destination


def main() -> None:
    args = parse_args()
    destination_root = Path(args.dest).expanduser().resolve()
    destination_root.mkdir(parents=True, exist_ok=True)
    selected_skills = args.skill or list(DEFAULT_SKILLS)

    installed_paths = []
    for skill_name in selected_skills:
        installed_paths.append(str(install_skill(skill_name, destination_root, args.overwrite)))

    print("Installed skills:")
    for path in installed_paths:
        print(f"- {path}")
    print("Restart Codex to pick up newly installed or updated skills.")


if __name__ == "__main__":
    main()
