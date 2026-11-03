"""Generate a curated anomalies dataset for integration testing."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


OUTPUT_PATH = Path("data/curated_anomalies.csv")
ROW_COUNT = 100
ANOMALY_COUNT = 10
DAILY_BURN_RATE = 500


def main() -> None:
    rng = np.random.default_rng(42)

    team_size = rng.integers(3, 11, size=ROW_COUNT)
    story_points = rng.choice([1, 2, 3, 5, 8, 13], size=ROW_COUNT)
    estimated_days = story_points * rng.uniform(1.5, 3.5, size=ROW_COUNT)
    estimated_days = np.maximum(2, np.round(estimated_days)).astype(int)

    actual_days = estimated_days * rng.normal(1.05, 0.12, size=ROW_COUNT)
    actual_days = np.maximum(1, np.round(actual_days)).astype(int)

    budget_allocated = estimated_days * DAILY_BURN_RATE
    cost_consumed = actual_days * DAILY_BURN_RATE

    is_true_anomaly = np.zeros(ROW_COUNT, dtype=int)
    anomaly_indices = rng.choice(ROW_COUNT, size=ANOMALY_COUNT, replace=False)

    for idx in anomaly_indices[: ANOMALY_COUNT // 2]:
        cost_consumed[idx] = int(budget_allocated[idx] * rng.uniform(1.8, 2.5))
        is_true_anomaly[idx] = 1

    for idx in anomaly_indices[ANOMALY_COUNT // 2 :]:
        actual_days[idx] = int(estimated_days[idx] * rng.uniform(1.8, 2.6))
        cost_consumed[idx] = actual_days[idx] * DAILY_BURN_RATE
        is_true_anomaly[idx] = 1

    df = pd.DataFrame(
        {
            "Story_Points": story_points,
            "Estimated_Days": estimated_days,
            "Actual_Days": actual_days,
            "Budget_Allocated": budget_allocated,
            "Cost_Consumed": cost_consumed,
            "Team_Size": team_size,
            "is_true_anomaly": is_true_anomaly,
        }
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(df)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
