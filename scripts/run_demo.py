"""Run the three presentation scenarios and print their LangGraph traces."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import get_settings  # noqa: E402
from graph import build_graph  # noqa: E402
from state import initial_state  # noqa: E402


def load_scenarios() -> list[dict]:
    with (ROOT / "data" / "demo_scenarios.json").open(encoding="utf-8") as handle:
        scenarios = json.load(handle)
    now = datetime.now(ZoneInfo(get_settings().timezone))
    hours = {"NOW_MINUS_2_HOURS": 2, "NOW_MINUS_5_HOURS": 5, "NOW_MINUS_8_HOURS": 8}
    for scenario in scenarios:
        marker = scenario["submission"]["catch_time"]
        scenario["submission"]["catch_time"] = (
            now - timedelta(hours=hours[marker])
        ).isoformat()
    return scenarios


def main() -> None:
    app = build_graph(with_memory=True)
    for scenario in load_scenarios():
        config = {"configurable": {"thread_id": str(uuid4())}}
        result = app.invoke(initial_state(scenario["submission"]), config=config)
        actual = result["decision"]["type"]
        marker = "PASS" if actual == scenario["expected_route"] else "FAIL"
        print(f"[{marker}] {scenario['name']}: {actual}")
        for event in result["execution_logs"]:
            print(f"  - {event['node']}: {event['message']}")
        print(f"  {result['final_response'].splitlines()[0]}")


if __name__ == "__main__":
    main()

