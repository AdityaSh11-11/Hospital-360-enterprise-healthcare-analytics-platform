import json
from datetime import datetime
from pathlib import Path

from generator.config import CONFIG


def get_existing_batches():

    directory = CONFIG.incremental_directory

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return sorted(
        [
            path
            for path in directory.iterdir()
            if path.is_dir()
            and path.name.startswith("BATCH-")
        ]
    )


def next_batch_id(
    business_date: str,
) -> str:

    date_part = business_date.replace(
        "-",
        "",
    )

    prefix = f"BATCH-{date_part}-"

    existing = [
        path.name
        for path in get_existing_batches()
        if path.name.startswith(prefix)
    ]

    sequence = len(existing) + 1

    return (
        f"{prefix}"
        f"{sequence:03d}"
    )


def create_batch_directory(
    batch_id: str,
) -> Path:

    path = (
        CONFIG.incremental_directory
        / batch_id
    )

    path.mkdir(
        parents=True,
        exist_ok=False,
    )

    return path


def save_manifest(
    batch_directory: Path,
    manifest: dict,
):

    path = (
        batch_directory
        / "manifest.json"
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            manifest,
            file,
            indent=4,
            default=str,
        )


def utc_timestamp():

    return datetime.utcnow().isoformat()