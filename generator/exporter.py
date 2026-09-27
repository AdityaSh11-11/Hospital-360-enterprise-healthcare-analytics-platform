from pathlib import Path

import pandas as pd

from generator.config import CONFIG
from utils.logger import get_logger


logger = get_logger(__name__)


def export_dataframe(
    dataframe: pd.DataFrame,
    filename: str,
) -> Path:

    directory = CONFIG.raw_directory

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = directory / filename

    dataframe.to_csv(
        path,
        index=False,
    )

    logger.info(
        "Exported %s rows to %s",
        len(dataframe),
        path,
    )

    return path