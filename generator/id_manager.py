import re
from pathlib import Path

import pandas as pd


def extract_numeric_id(
    value: str,
) -> int:

    if pd.isna(value):
        return 0

    match = re.search(
        r"(\d+)$",
        str(value),
    )

    if not match:
        return 0

    return int(
        match.group(1)
    )


def max_id_from_csv(
    path: Path,
    column: str,
) -> int:

    if not path.exists():
        return 0

    df = pd.read_csv(
        path,
        usecols=[column],
    )

    if df.empty:
        return 0

    return max(
        extract_numeric_id(value)
        for value in df[column]
    )


def max_id_from_files(
    paths: list[Path],
    column: str,
) -> int:

    maximum = 0

    for path in paths:

        if not path.exists():
            continue

        try:

            current = max_id_from_csv(
                path,
                column,
            )

            maximum = max(
                maximum,
                current,
            )

        except ValueError:
            continue

    return maximum