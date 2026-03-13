from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd
from odps import ODPS


@dataclass
class OdpsConfig:
    access_id: str
    access_key: str
    project: str
    endpoint: str


class OdpsClient:
    def __init__(self, config: OdpsConfig):
        self.config = config
        self.odps = ODPS(
            config.access_id,
            config.access_key,
            config.project,
            endpoint=config.endpoint,
        )

    def run_sql(self, sql: str, limit: int = 2000) -> pd.DataFrame:
        instance = self.odps.execute_sql(sql)
        with instance.open_reader() as reader:
            try:
                return reader.to_pandas(n=limit)
            except TypeError:
                df = reader.to_pandas()
                if limit and len(df) > limit:
                    return df.head(limit)
                return df

    def run_script(self, sql: str) -> None:
        self.odps.execute_sql(f"SET odps.sql.submit.mode=script; {sql}")
