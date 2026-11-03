import pandas as pd
import pytest

from src.forecasting import ProjectForecaster


@pytest.mark.integration
@pytest.mark.slow
def test_phase2_forecasting_mape_target() -> None:
    import numpy as np
    # Generate clean synthetic series (linear trend + weekly seasonality) for robust forecasting test
    ds = pd.date_range(start="2021-01-01", periods=150, freq="D")
    y = [float(10.0 + 0.05 * i + 2.0 * np.sin(2 * np.pi * i / 7.0)) for i in range(150)]
    ts_df = pd.DataFrame({"ds": ds, "y": y})

    forecaster = ProjectForecaster(enable_sprint_seasonality=True)
    result = forecaster.generate_forecast(
        ts_df,
        metric_column="y",
        periods=30,
        include_metrics=True,
        include_components=True,
        date_column="ds",
    )

    metrics = result["metrics"]
    forecast_df = result["forecast"]

    assert metrics is not None
    assert metrics["mape"] is not None
    assert metrics["mape"] <= 15.0
    assert len(forecast_df) == len(ts_df) + 30
    assert {"ds", "yhat", "yhat_lower", "yhat_upper"}.issubset(forecast_df.columns)
