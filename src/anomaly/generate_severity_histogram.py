"""Generate Phase 2 anomaly severity distribution figure."""

import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.anomaly.anomaly_detector import AnomalyEngine


LOGGER = logging.getLogger("anomaly")


def configure_logging() -> None:
    """Configure structured logging for severity figure generation."""
    log_file = PROJECT_ROOT / "logs" / "anomaly_audit.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    if LOGGER.handlers:
        return

    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    LOGGER.setLevel(logging.INFO)
    LOGGER.addHandler(file_handler)
    LOGGER.addHandler(stream_handler)
    LOGGER.propagate = False


def main() -> None:
    """Run anomaly severity distribution workflow."""
    configure_logging()

    data_path = PROJECT_ROOT / "data" / "ml_ready_data.csv"
    report_path = PROJECT_ROOT / "reports" / "fig_phase2_b_severity_dist.png"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(data_path)
    df["budget_overrun_pct"] = (
        (df["Cost_Consumed"] - df["Budget_Allocated"]) / df["Budget_Allocated"] * 100
    )
    df["days_overrun_pct"] = (
        (df["Actual_Days"] - df["Estimated_Days"]) / df["Estimated_Days"] * 100
    )
    df["efficiency_score"] = df["Estimated_Days"] / df["Actual_Days"]
    df["cost_efficiency"] = df["Budget_Allocated"] / df["Cost_Consumed"]

    feature_columns = [
        "Story_Points",
        "Estimated_Days",
        "Actual_Days",
        "Budget_Allocated",
        "Cost_Consumed",
        "budget_overrun_pct",
        "days_overrun_pct",
        "efficiency_score",
        "cost_efficiency",
    ]

    features_df = df[feature_columns].replace([np.inf, -np.inf], np.nan).dropna().copy()

    engine = AnomalyEngine(contamination=0.03)
    results = engine.detect_anomalies(features_df, feature_columns)

    order = ["High", "Medium", "Low", "Normal"]
    counts = results["severity"].value_counts().reindex(order, fill_value=0)
    colors = ["#b22222", "#ff8c00", "#f0c419", "#2e8b57"]

    fig, ax = plt.subplots(figsize=(10, 8))
    bars = ax.bar(
        counts.index, counts.values, color=colors, edgecolor="black", alpha=0.9
    )

    total = int(counts.sum())
    for bar, value in zip(bars, counts.values):
        pct = (value / total * 100) if total > 0 else 0
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value}\n({pct:.1f}%)",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    ax.set_title("Anomaly Severity Distribution (Phase 2)")
    ax.set_xlabel("Severity Level")
    ax.set_ylabel("Count")
    ax.grid(axis="y", linestyle="--", alpha=0.35)

    fig.tight_layout()
    fig.savefig(report_path, dpi=300)
    plt.close(fig)

    LOGGER.info("Severity distribution figure generated - counts: %s", counts.to_dict())
    print(f"Severity counts: {counts.to_dict()}")


if __name__ == "__main__":
    main()
