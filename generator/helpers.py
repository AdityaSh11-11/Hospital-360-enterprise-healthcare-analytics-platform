import random
from datetime import datetime, timedelta

import numpy as np

from generator.config import CONFIG


def set_random_seed() -> None:
    """
    Makes generated datasets reproducible.
    """

    random.seed(CONFIG.random_seed)
    np.random.seed(CONFIG.random_seed)


def random_date(
    start: datetime,
    end: datetime,
) -> datetime:

    if start > end:
        raise ValueError(
            "Start date cannot be after end date."
        )

    seconds = int(
        (end - start).total_seconds()
    )

    offset = random.randint(
        0,
        max(seconds, 0),
    )

    return start + timedelta(
        seconds=offset
    )


def money(value: float) -> float:
    return round(
        max(float(value), 0.0),
        2,
    )


def weighted_choice(
    values,
    weights,
):
    return random.choices(
        values,
        weights=weights,
        k=1,
    )[0]