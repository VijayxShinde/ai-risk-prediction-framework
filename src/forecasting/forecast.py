"""
Time-Series Forecasting Module
AI-Driven Risk Prediction Framework - Phase 2

Implements Prophet-based forecasting for project metrics with enhanced capabilities
including sprint seasonality, forecast accuracy metrics, and structured logging.
"""

import logging
import warnings
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
import os

import pandas as pd
import numpy as np
from prophet import Prophet
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error, r2_score

# Configure structured logger for IEEE tracking
logger = logging.getLogger('forecasting')
logger.setLevel(logging.INFO)

if not logger.handlers:
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.propagate = False

# Configuration constants
DEFAULT_CONFIG = {
    'growth': 'linear',
    'changepoint_prior_scale': 0.05,
    'seasonality_prior_scale': 10,
    'daily_seasonality': False,
    'weekly_seasonality': True,
    'yearly_seasonality': False,
    'sprint_period': 14,
    'sprint_fourier_order': 3
}

# Validation thresholds
MIN_DATA_POINTS = 2
RECOMMENDED_DATA_POINTS = 30
MAX_FORECAST_HORIZON = 90

# Confidence intervals
CONFIDENCE_INTERVALS = [0.80, 0.95]


class InsufficientDataError(Exception):
    """Raised when data has fewer than minimum required points."""
    pass


class ProphetFittingError(Exception):
    """Raised when Prophet model fails to fit."""
    pass


class InvalidMetricColumnError(Exception):
    """Raised when specified metric column is missing or invalid."""
    pass


class ProjectForecaster:
    """
    Enhanced Prophet-based time-series forecasting engine for project metrics.
    
    Implements Phase 2 Feature F2-A: Time-Series Forecasting Engine with:
    - Sprint seasonality modeling (14-day cycles, Fourier order 3)
    - Forecast accuracy metrics (MAPE, RMSE, R²)
    - Auto-date normalization for datasets without date columns
    - Structured logging for IEEE paper tracking
    - Error handling for insufficient data, missing columns, fitting failures
    """
    
    def __init__(
        self, 
        config: Optional[Dict] = None,
        enable_sprint_seasonality: bool = True,
        logger_name: str = 'forecasting'
    ):
        """
        Initialize the ProjectForecaster.
        
        Args:
            config: Custom Prophet configuration (overrides defaults)
            enable_sprint_seasonality: Add 14-day sprint cycle seasonality
            logger_name: Logger identifier for tracking
        """
        self.config = DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)
            
        self.enable_sprint_seasonality = enable_sprint_seasonality
        self.logger = logging.getLogger(logger_name)
        
        # Add model if sprint seasonality enabled
        if enable_sprint_seasonality:
            self.logger.info(
                f"Initialized Prophet with sprint seasonality (period={self.config['sprint_period']})"
            )
        else:
            self.logger.info("Initialized Prophet without sprint seasonality")
    
    def generate_forecast(
        self,
        data: pd.DataFrame,
        metric_column: str,
        periods: int = 30,
        include_metrics: bool = True,
        include_components: bool = False,
        date_column: str = 'date'
    ) -> Dict:
        """
        Generate time-series forecast for specified metric.
        
        Args:
            data: DataFrame with time-series data
            metric_column: Column name to forecast (e.g., 'cost_overrun')
            periods: Future periods to forecast (default: 30 days)
            include_metrics: Calculate MAPE, RMSE, R² (default: True)
            include_components: Include trend/seasonality decomposition
            date_column: Name of date column (default: 'date')
            
        Returns:
            Dictionary with:
                - 'forecast': DataFrame(ds, yhat, yhat_lower, yhat_upper)
                - 'model': Fitted Prophet object
                - 'metrics': Dict(mape, rmse, r2) [if include_metrics=True]
                - 'components': DataFrame [if include_components=True]
                - 'metadata': Dict(training_periods, forecast_periods, etc.)
                
        Raises:
            InsufficientDataError: < 2 data points
            InvalidMetricColumnError: metric_column not found
            ProphetFittingError: Model training failure
        """
        try:
            self._validate_data(data, metric_column)
        except Exception as e:
            self.logger.error(f"Forecasting failed: {str(e)}")
            raise
        
        self.logger.info(f"Starting forecast generation for metric '{metric_column}'")

        # Normalize dates if needed
        df_normalized = self._normalize_dates(data, date_column)

        # Prepare Prophet format (ds, y)
        df_prophet = self._prepare_prophet_data(df_normalized, metric_column, date_column)

        # Initialize and fit model
        model = self._initialize_model()
        model = self._fit_model(df_prophet, model)
        
        # Generate forecast
        future = model.make_future_dataframe(periods=periods)
        forecast = model.predict(future)
        
        # Extract required columns
        forecast_output = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
        
        # Calculate metrics if requested
        metrics = None
        if include_metrics and len(df_prophet) >= 10:  # Need sufficient data for split
            metrics = self._calculate_metrics(model, df_prophet)
        
        # Extract components if requested
        components = None
        if include_components:
            components = self._extract_components(model, forecast)
        
        # Build metadata
        metadata = self._build_metadata(df_prophet, periods, model)
        
        result = {
            'forecast': forecast_output,
            'model': model,
            'metadata': metadata
        }
        
        if include_metrics:
            result['metrics'] = metrics
            
        if include_components:
            result['components'] = components
            
        self.logger.info(f"Forecast generated: {periods} periods ahead")
        return result
    
    def _validate_data(self, data: pd.DataFrame, metric_column: str) -> None:
        """Validate input data meets requirements."""
        # Check minimum data points
        if len(data) < MIN_DATA_POINTS:
            raise InsufficientDataError(
                f"Prophet requires at least {MIN_DATA_POINTS} data points, got {len(data)}"
            )
        
        # Check required columns
        if metric_column not in data.columns:
            raise InvalidMetricColumnError(f"Column '{metric_column}' not found in DataFrame")
        
        # Check for null values
        if data[metric_column].isnull().any():
            self.logger.warning(
                f"Null values found in '{metric_column}', will be dropped"
            )
    
    def _normalize_dates(
        self, 
        data: pd.DataFrame, 
        date_column: str
    ) -> pd.DataFrame:
        """
        Auto-generate normalized dates if missing.
        
        Strategy:
        - If date_column exists: parse and validate
        - If missing: generate sequential dates starting from today
        - Normalize to daily frequency with forward-fill for gaps
        """
        df = data.copy()
        
        if date_column in df.columns:
            # Existing dates: validate format and fill gaps
            df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
            
            if df[date_column].isnull().any():
                self.logger.warning(
                    f"Invalid dates detected, filling gaps"
                )
                # Fill with sequential dates
                n_rows = len(df)
                end_date = pd.Timestamp.today()
                start_date = end_date - pd.Timedelta(days=n_rows - 1)
                
                df[date_column] = pd.date_range(
                    start=start_date,
                    periods=n_rows,
                    freq='D'
                )
                
                self.logger.info(
                    f"Generated dates: {start_date.date()} to {end_date.date()}"
                )
        else:
            # No dates: generate from today backwards
            self.logger.info(
                f"No '{date_column}' column found, generating normalized dates"
            )
            
            # Use row count to determine date range
            n_rows = len(df)
            end_date = pd.Timestamp.today()
            start_date = end_date - pd.Timedelta(days=n_rows - 1)
            
            df[date_column] = pd.date_range(
                start=start_date,
                periods=n_rows,
                freq='D'
            )
            
            self.logger.info(
                f"Generated dates: {start_date.date()} to {end_date.date()}"
            )
        
        # Ensure chronological order
        df = df.sort_values(date_column).reset_index(drop=True)
        
        return df
    
    def _prepare_prophet_data(
        self,
        data: pd.DataFrame,
        metric_column: str,
        date_column: str
    ) -> pd.DataFrame:
        """Transform to Prophet's required ds/y format."""
        df = data[[date_column, metric_column]].copy()
        df = df.dropna()
        df.columns = ['ds', 'y']
        df['ds'] = pd.to_datetime(df['ds'])
        return df
    
    def _initialize_model(self) -> Prophet:
        """Create Prophet model with enhanced configuration."""
        model = Prophet(
            growth=self.config['growth'],
            changepoint_prior_scale=self.config['changepoint_prior_scale'],
            seasonality_prior_scale=self.config['seasonality_prior_scale'],
            daily_seasonality=self.config['daily_seasonality'],
            weekly_seasonality=self.config['weekly_seasonality'],
            yearly_seasonality=self.config['yearly_seasonality']
        )
        
        # Add custom sprint seasonality if enabled
        if self.enable_sprint_seasonality:
            model.add_seasonality(
                name='sprint',
                period=self.config['sprint_period'],
                fourier_order=self.config['sprint_fourier_order']
            )
            self.logger.info("Added sprint seasonality (14-day cycles)")
        
        return model
    
    def _fit_model(self, df_prophet: pd.DataFrame, model: Prophet) -> Prophet:
        """Fit Prophet model with error handling."""
        try:
            model.fit(df_prophet)
            self.logger.info("Model fitted successfully")
            return model
        except Exception as e:
            raise ProphetFittingError(f"Model fitting failed: {str(e)}")
    
    def _calculate_metrics(
        self,
        model: Prophet,
        df_prophet: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Calculate forecast accuracy metrics via backtesting.
        
        Uses last 20% of data as validation set.
        
        Returns:
            Dict with mape, rmse, r2 scores
        """
        # Split data
        split_idx = int(len(df_prophet) * 0.8)
        train = df_prophet[:split_idx]
        test = df_prophet[split_idx:]
        
        if len(test) < 2:
            self.logger.warning("Insufficient test data for metrics, skipping")
            return {'mape': None, 'rmse': None, 'r2': None}
        
        # Retrain on training set only
        temp_model = Prophet()
        if self.enable_sprint_seasonality:
            temp_model.add_seasonality(
                name='sprint',
                period=self.config['sprint_period'],
                fourier_order=self.config['sprint_fourier_order']
            )
        temp_model.fit(train)
        
        # Predict on test set
        future = temp_model.make_future_dataframe(periods=len(test))
        forecast = temp_model.predict(future)
        
        # Extract predictions for test period
        y_true = test['y'].values
        y_pred = forecast.iloc[-len(test):]['yhat'].values
        
        # Calculate metrics
        mape = mean_absolute_percentage_error(y_true, y_pred) * 100
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        r2 = r2_score(y_true, y_pred)
        
        self.logger.info(f"Validation Metrics - MAPE: {mape:.2f}%, RMSE: {rmse:.2f}, R²: {r2:.3f}")
        
        return {
            'mape': round(mape, 2),
            'rmse': round(rmse, 2),
            'r2': round(r2, 4)
        }
    
    def _extract_components(
        self,
        model: Prophet,
        forecast: pd.DataFrame
    ) -> pd.DataFrame:
        """Extract trend and seasonality components."""
        available_cols = ['ds', 'trend', 'yhat']
        if 'weekly' in forecast.columns:
            available_cols.append('weekly')
        if 'sprint' in forecast.columns:
            available_cols.append('sprint')
        return forecast[available_cols].copy()
    
    def _build_metadata(
        self,
        df_prophet: pd.DataFrame,
        periods: int,
        model: Prophet
    ) -> Dict:
        """Compile model metadata for audit trail."""
        return {
            'training_periods': len(df_prophet),
            'forecast_periods': periods,
            'seasonalities': ['weekly', 'sprint'] if self.enable_sprint_seasonality else ['weekly'],
            'training_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }