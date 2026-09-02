import json
import sys
import tempfile
import unittest
from pathlib import Path

# Supports both `python tests/test_pipeline.py` (common in VS Code) and
# `python -m unittest discover -s tests` from the repository root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import run
from src.warehouse import Warehouse


class PipelineTests(unittest.TestCase):
    def test_rejects_invalid_and_deduplicates_replayed_events(self):
        with tempfile.TemporaryDirectory() as directory:
            feed = Path(directory) / "feed.jsonl"
            good = {"event_id":"one","game_id":"g","event_ts":"2024-09-05T00:00:00Z","season":2024,"week":1,"home_team":"KC","away_team":"BAL","posteam":"KC","qtr":1,"game_clock":"15:00","play_type":"run","yards_gained":5,"home_score":0,"away_score":0}
            feed.write_text("\n".join([json.dumps(good), json.dumps(good), "{bad json"]))
            database = str(Path(directory) / "db.sqlite")
            result = run(str(feed), database)
            self.assertEqual(result, {"raw_events": 1, "play_facts": 1, "rejected_events": 1, "game_live_metrics": 1})
            warehouse = Warehouse(database)
            self.assertEqual(warehouse.scoreboard()[0]["total_plays"], 1)
            warehouse.close()


if __name__ == "__main__":
    unittest.main()
