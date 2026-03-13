from __future__ import annotations

import os
from datetime import datetime
from typing import Optional


def write_report(content: str, reports_dir: str, output_path: Optional[str] = None) -> str:
    os.makedirs(reports_dir, exist_ok=True)
    if output_path:
        path = output_path
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(reports_dir, f"report_{ts}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path
