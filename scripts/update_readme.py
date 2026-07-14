#!/usr/bin/env python3
"""Generate profile README activity sections from Markdown files in logs/."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
LOGS_DIR = ROOT / "logs"

ACTIVITY_START = "<!-- dev_activity starts -->"
ACTIVITY_END = "<!-- dev_activity ends -->"
LOG_START = "<!-- dev_log starts -->"
LOG_END = "<!-- dev_log ends -->"

MAX_ACTIVITY_ITEMS = 6
MAX_LOG_ROWS = 7


@dataclass(frozen=True)
class DevLog:
    date: str
    path: Path
    activities: tuple[str, ...]


def read_logs() -> list[DevLog]:
    if not LOGS_DIR.exists():
        return []

    logs: list[DevLog] = []
    for path in sorted(LOGS_DIR.glob("*.md"), reverse=True):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", path.stem):
            continue

        activities = tuple(
            line.strip()[2:].strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith("- ") and line.strip()[2:].strip()
        )
        logs.append(DevLog(date=path.stem, path=path, activities=activities))

    return logs


def activity_icon(text: str) -> str:
    value = text.lower()
    if any(word in value for word in ("fix", "bug", "repair", "resolve")):
        return "🛠️"
    if any(word in value for word in ("ship", "release", "deploy", "launch")):
        return "🚀"
    if any(word in value for word in ("build", "add", "create", "implement")):
        return "✨"
    if any(word in value for word in ("review", "audit", "check")):
        return "🔎"
    if any(word in value for word in ("learn", "explore", "experiment", "research")):
        return "🧪"
    return "📝"


def markdown_link(log: DevLog) -> str:
    relative = log.path.relative_to(ROOT).as_posix()
    return f"[{log.date}]({relative})"


def render_activity(logs: list[DevLog]) -> str:
    rows: list[str] = []
    for log in logs:
        for activity in log.activities:
            rows.append(
                f"- {activity_icon(activity)} **{markdown_link(log)}** — {activity}"
            )
            if len(rows) >= MAX_ACTIVITY_ITEMS:
                return "\n".join(rows)

    return "\n".join(rows) if rows else "_No development activity logged yet._"


def escape_table(value: str) -> str:
    return value.replace("|", r"\|").replace("\n", " ").strip()


def render_log_table(logs: list[DevLog]) -> str:
    if not logs:
        return "_No development logs yet._"

    rows = [
        "| Date | Highlight |",
        "| --- | --- |",
    ]

    for log in logs[:MAX_LOG_ROWS]:
        highlight = log.activities[0] if log.activities else "Development log updated"
        rows.append(f"| {markdown_link(log)} | {escape_table(highlight)} |")

    return "\n".join(rows)


def replace_section(source: str, start: str, end: str, body: str) -> str:
    pattern = re.compile(
        rf"{re.escape(start)}.*?{re.escape(end)}",
        flags=re.DOTALL,
    )
    replacement = f"{start}\n\n{body.rstrip()}\n\n{end}"

    if not pattern.search(source):
        raise RuntimeError(f"README marker pair not found: {start} / {end}")

    return pattern.sub(replacement, source, count=1)


def main() -> None:
    logs = read_logs()
    readme = README_PATH.read_text(encoding="utf-8")

    readme = replace_section(
        readme,
        ACTIVITY_START,
        ACTIVITY_END,
        render_activity(logs),
    )
    readme = replace_section(
        readme,
        LOG_START,
        LOG_END,
        render_log_table(logs),
    )

    README_PATH.write_text(readme.rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
