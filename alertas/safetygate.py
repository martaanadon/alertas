"""EU Safety Gate (non-food products) -- discovery stage.

The Commission's portal exposes a public weekly-report export. Its exact
schema is not documented publicly, so this first version only downloads and
stores the raw export. Once the first run has saved real files, the agent
writes the parser against them (see agent/BACKLOG.md). Nothing from here is
published until that parser exists and has tests.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

WEEKLY_LIST = "https://ec.europa.eu/safety-gate-alerts/api/download/weeklyReport/list/xml/en"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; alertas-consumo-bot/0.1; open-data reuse)"}


def discover(raw_dir: Path) -> dict:
    raw_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    result = {"fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "url": WEEKLY_LIST}
    try:
        r = requests.get(WEEKLY_LIST, headers=HEADERS, timeout=60)
        result["status"] = r.status_code
        result["content_type"] = r.headers.get("content-type")
        result["bytes"] = len(r.content)
        if r.ok:
            (raw_dir / f"weekly_list_{stamp}.xml").write_bytes(r.content)
    except Exception as e:
        result["error"] = str(e)
    (raw_dir / "last_discovery.json").write_text(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    print(json.dumps(discover(Path("data/raw/safetygate")), indent=2))
