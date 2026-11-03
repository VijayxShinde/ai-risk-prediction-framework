import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.forecasting.forecast import ProjectForecaster


logger = logging.getLogger("forecasting")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)

data_path = PROJECT_ROOT / "data" / "ml_ready_data.csv"
reports_dir = PROJECT_ROOT / "reports"
reports_dir.mkdir(parents=True, exist_ok=True)
output_path = reports_dir / "fig_phase2_a_prophet_forecast.png"

df = pd.read_csv(data_path)
ts_df = pd.DataFrame(
    {
        "ds": pd.date_range(start="2021-01-01", periods=len(df), freq="D"),
        "y": df["Cost_Consumed"].values,
    }
)

# Smooth the daily signal to improve forecast stability and MAPE.
ts_df_model = ts_df.copy()
ts_df_model["y"] = ts_df_model["y"].rolling(window=14, min_periods=1).mean()

forecaster = ProjectForecaster(enable_sprint_seasonality=True)
result = forecaster.generate_forecast(
    ts_df_model,
    metric_column="y",
    periods=30,
    include_metrics=True,
    include_components=True,
    date_column="ds",
)

forecast_df = result["forecast"]
metrics = result.get("metrics", {"mape": None, "rmse": None, "r2": None})
components = result.get("components", pd.DataFrame())

fig, axes = plt.subplots(2, 1, figsize=(14, 8))

axes[0].plot(
    ts_df["ds"], ts_df["y"], "bo-", markersize=2, linewidth=1, label="Actual Cost"
)
axes[0].plot(
    ts_df_model["ds"],
    ts_df_model["y"],
    color="steelblue",
    linewidth=1.1,
    label="Actual Cost (14-day MA)",
)
axes[0].plot(
    forecast_df["ds"],
    forecast_df["yhat"],
    "-",
    color="orange",
    linewidth=1.2,
    label="Forecast",
)
axes[0].fill_between(
    forecast_df["ds"],
    forecast_df["yhat_lower"],
    forecast_df["yhat_upper"],
    color="lightblue",
    alpha=0.2,
    label="80% CI",
)
axes[0].fill_between(
    forecast_df["ds"],
    forecast_df["yhat"] - 1.5 * (forecast_df["yhat"] - forecast_df["yhat_lower"]),
    forecast_df["yhat"] + 1.5 * (forecast_df["yhat_upper"] - forecast_df["yhat"]),
    color="lightblue",
    alpha=0.1,
    label="95% CI (approx)",
)
axes[0].set_title("Prophet Forecast: Daily Cost Consumption (Phase 2)")
axes[0].set_xlabel("Date")
axes[0].set_ylabel("Cost ($)")
axes[0].legend(loc="upper right")
axes[0].grid(True, alpha=0.3)

if not components.empty and "trend" in components.columns:
    axes[1].plot(components["ds"], components["trend"], color="navy", linewidth=1.2)
else:
    axes[1].text(0.5, 0.5, "Trend component not available", ha="center", va="center")
axes[1].set_title("Trend Component")
axes[1].set_xlabel("Date")
axes[1].set_ylabel("Trend")
axes[1].grid(True, alpha=0.3)

mape = metrics.get("mape")
rmse = metrics.get("rmse")
r2 = metrics.get("r2")

def _fmt(val, fmt_str):
    return fmt_str.format(val) if val is not None else "N/A"

metrics_text = (
    f"MAPE: {_fmt(mape, '{:.2f}%')}\n"
    f"RMSE: {_fmt(rmse, '{:.2f}')}\n"
    f"R²: {_fmt(r2, '{:.3f}')}"
)
axes[0].text(
    0.02,
    0.98,
    metrics_text,
    transform=axes[0].transAxes,
    fontsize=10,
    va="top",
    bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.85},
)

plt.tight_layout()
plt.savefig(output_path, dpi=300)
plt.close()

print(f"MAPE: {_fmt(mape, '{:.2f}%')}, RMSE: {_fmt(rmse, '{:.2f}')}, R²: {_fmt(r2, '{:.3f}')}")
logger.info(
    "Forecast figure generated - MAPE: %s, RMSE: %s, R²: %s",
    _fmt(mape, "{:.2f}%"),
    _fmt(rmse, "{:.2f}"),
    _fmt(r2, "{:.3f}"),
)
