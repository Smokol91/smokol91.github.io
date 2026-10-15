
import json
import os
import re
import subprocess

from datetime import datetime
from pathlib import Path


LIVE = Path("live.json")
ARCHIVE = Path("transmisje.json")


def previous_version(commit):
    if not commit or set(commit) == {"0"}:
        return None

    result = subprocess.run(
        ["git", "show", f"{commit}:live.json"],
        capture_output=True,
        text=True
    )

    if result.returncode:
        return None

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def video_id(data):
    if not isinstance(data, dict):
        return ""

    return str(data.get("videoId") or "").strip()


def create_entry(old):
    date = str(old.get("start") or "")[:10]

    try:
        displayed = datetime.strptime(
            date, "%Y-%m-%d"
        ).strftime("%d.%m.%Y")
    except ValueError:
        raise ValueError(
            "Poprzedni live nie posiada poprawnej daty start."
        )

    return {
        "date": date,
        "displayDate": displayed,
        "game": str(old.get("game") or ""),
        "episode": re.sub(
            r"<[^>]*>", "",
            str(old.get("episode") or "")
        ).strip(),
        "title": str(old.get("title") or ""),
        "videoId": video_id(old),
        "description": str(old.get("description") or "")
    }


def main():
    old = previous_version(
        os.environ.get("BEFORE_SHA", "")
    )

    current = json.loads(
        LIVE.read_text(encoding="utf-8")
    )

    if (
        not old
        or not video_id(old)
        or video_id(old) == video_id(current)
    ):
        print("Brak zmiany videoId.")
        return

    entries = json.loads(
        ARCHIVE.read_text(encoding="utf-8")
    )

    if not isinstance(entries, list):
        raise TypeError(
            "transmisje.json musi zawierac tablice."
        )

    entry = create_entry(old)

    entries = [
        item for item in entries
        if video_id(item) != entry["videoId"]
    ]

    entries.append(entry)

    entries.sort(
        key=lambda item: str(item.get("date") or ""),
        reverse=True
    )

    ARCHIVE.write_text(
        json.dumps(
            entries,
            ensure_ascii=False,
            indent=2
        ) + "\n",
        encoding="utf-8"
    )

    print(
        f"Zarchiwizowano: {entry['videoId']}"
    )


if __name__ == "__main__":
    main()
