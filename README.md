# NFL Game Day ETL Pipeline

A small, runnable ETL project that models an NFL game-day data platform. It ingests play events, validates and normalizes them, stores raw and curated records in SQLite, and maintains live game and team aggregates after every event.

## What it does

```text
JSONL game feed -> extract + validate -> normalize -> SQLite raw/curated layers -> live scoreboard
```

- **Extract** — streams newline-delimited JSON (JSONL), so it works with a growing live feed or replay file.
- **Transform** — rejects malformed records, deduplicates events, normalizes team codes, derives game state, and calculates expected-points change.
- **Load** — stores immutable raw payloads, typed play facts, data-quality rejects, and continuously updated game/team aggregates.
- **Serve** — prints a live scoreboard and pipeline run summary.

The included `data/nfl_game_events.jsonl` is a compact NFL-style game-day dataset for repeatable local development. The schema is compatible with a feed adapter for a larger source such as nflverse play-by-play data.

## Quick start

Requires Python 3.11+ and no third-party packages.

```bash
python -m src.pipeline --feed data/nfl_game_events.jsonl --database state/gameday.db --reset
python -m src.dashboard --database state/gameday.db
python -m unittest discover -s tests -v
```

## Running in “real-time” replay mode

This replays each event with a short delay, showing the scoreboard update as the game progresses:

```bash
python -m src.pipeline --feed data/nfl_game_events.jsonl --database state/gameday.db --reset --replay-delay 0.5
```

## Data contract

Every event must contain: `event_id`, `game_id`, `event_ts`, `season`, `week`, `home_team`, `away_team`, `posteam`, `qtr`, `game_clock`, `play_type`, `yards_gained`, `home_score`, and `away_score`.

`event_id` is the idempotency key. Re-running a feed never duplicates a play. Invalid records are captured in `rejected_events` instead of crashing the stream.

## Project layout

```text
data/       Example NFL game-day event feed
src/        ETL pipeline, warehouse and dashboard
tests/      Contract and idempotency tests
state/      Local SQLite database (created at runtime)
```

## Adapting to production

1. Replace `JsonlEventSource` with a Kafka, Kinesis, webhook, or provider API adapter.
2. Use the provider's play identifier as `event_id` and retain its original payload in `raw_events`.
3. Move SQLite to a warehouse (Postgres/BigQuery/Snowflake) and schedule compaction/partitioning by `season`, `week`, and `game_id`.
4. Publish `game_live_metrics` to a BI dashboard or API after each successful transaction.

The database schema is intentionally compact but separates raw, curated, rejected, and aggregate layers, preserving auditability as the feed evolves.
