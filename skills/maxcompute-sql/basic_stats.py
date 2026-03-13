from __future__ import annotations

from typing import Any, Dict

import pandas as pd


def _describe_numeric(df: pd.DataFrame) -> Dict[str, Any]:
    numeric = df.select_dtypes(include=["number"])
    if numeric.empty:
        return {}
    desc = numeric.describe().to_dict()
    return {k: {stat: float(val) for stat, val in v.items()} for k, v in desc.items()}


def run(dataframe: pd.DataFrame, max_rows: int = 5) -> Dict[str, Any]:
    if dataframe is None or dataframe.empty:
        return {"rows": 0, "columns": [], "sample": []}
    sample = dataframe.head(max_rows).to_dict(orient="records")
    return {
        "rows": int(len(dataframe)),
        "columns": list(dataframe.columns),
        "sample": sample,
        "numeric_describe": _describe_numeric(dataframe),
    }


SKILL = {
    "name": "basic_stats",
    "description": "Summarize the latest query result: rows, columns, sample, numeric describe.",
    "inputs": {
        "dataframe": "pandas.DataFrame (auto-injected)",
        "max_rows": "int (optional, default 5)",
    },
    "run": run,
}
