"""
Forecasting Engine - Mathematical Predictions
Pure statistical methods without AI/LLM dependencies

Methods:
- Linear Regression (Trend Extrapolation)
- Exponential Smoothing (Weighted Recent Data)
- Moving Average Forecast
- Seasonal Decomposition
- Growth Rate Projection
"""

from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime, timedelta
import numpy as np
import pandas as pd


class ForecastEngine:
    """
    Mathematical forecasting engine for time series data.
    All methods are deterministic and explainable.
    """
    
    def __init__(self, data: pd.DataFrame, date_column: str = 'Date', 
                 value_column: str = 'Amount'):
        """
        Initialize the forecast engine.
        
        Args:
            data: DataFrame with time series data
            date_column: Name of the date column
            value_column: Name of the value column to forecast
        """
        self.raw_data = data.copy()
        self.date_column = date_column
        self.value_column = value_column
        
        # Prepare monthly aggregated data
        self.monthly_data = self._prepare_monthly_data()
    
    def _prepare_monthly_data(self) -> pd.DataFrame:
        """Aggregate data to monthly level."""
        if self.raw_data.empty:
            return pd.DataFrame(columns=['Period', 'Amount', 'Year', 'Month'])
        
        df = self.raw_data.copy()
        df['Period'] = df[self.date_column].dt.to_period('M')
        df['Year'] = df[self.date_column].dt.year
        df['Month'] = df[self.date_column].dt.month
        
        monthly = df.groupby(['Period', 'Year', 'Month'])[self.value_column].sum().reset_index()
        monthly = monthly.sort_values('Period')
        monthly['PeriodIndex'] = range(len(monthly))
        
        return monthly
    
    # =========================================================================
    # Linear Regression Forecast
    # =========================================================================
    
    def linear_regression_forecast(self, periods: int = 6) -> Dict[str, Any]:
        """
        Forecast using linear regression (least squares).
        
        Formula: y = mx + b
        - m: slope (trend direction)
        - b: y-intercept
        
        Args:
            periods: Number of periods to forecast
            
        Returns:
            Dict with forecast data, confidence, and parameters
        """
        if len(self.monthly_data) < 3:
            return self._empty_forecast("Mindestens 3 Monate Daten erforderlich")
        
        x = self.monthly_data['PeriodIndex'].values
        y = self.monthly_data['Amount'].values
        
        # Calculate linear regression coefficients
        n = len(x)
        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_x2 = np.sum(x ** 2)
        
        # Slope (m) and intercept (b)
        m = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        b = (sum_y - m * sum_x) / n
        
        # R-squared (coefficient of determination)
        y_pred = m * x + b
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Standard error for confidence interval
        std_error = np.sqrt(ss_res / (n - 2)) if n > 2 else 0
        
        # Generate forecast
        last_period = self.monthly_data['Period'].iloc[-1]
        forecast_periods = []
        forecast_values = []
        confidence_lower = []
        confidence_upper = []
        
        for i in range(1, periods + 1):
            future_x = len(x) - 1 + i
            forecast_y = m * future_x + b
            
            # Confidence interval (±1.96 std error for 95%)
            margin = 1.96 * std_error * np.sqrt(1 + 1/n + (future_x - np.mean(x))**2 / sum_x2)
            
            # Calculate future period
            future_period = last_period + i
            
            forecast_periods.append(str(future_period))
            forecast_values.append(max(0, forecast_y))  # No negative forecasts
            confidence_lower.append(max(0, forecast_y - margin))
            confidence_upper.append(forecast_y + margin)
        
        # Trend interpretation
        monthly_change = m
        annual_change = m * 12
        trend_direction = "steigend" if m > 0 else ("fallend" if m < 0 else "stabil")
        
        return {
            'method': 'Lineare Regression',
            'periods': forecast_periods,
            'values': forecast_values,
            'confidence_lower': confidence_lower,
            'confidence_upper': confidence_upper,
            'parameters': {
                'slope': m,
                'intercept': b,
                'r_squared': r_squared,
                'monthly_change': monthly_change,
                'annual_change': annual_change,
            },
            'interpretation': {
                'trend': trend_direction,
                'confidence': r_squared,
                'message': f"Trend: {trend_direction} (R²={r_squared:.2%}), "
                          f"Ø monatliche Änderung: €{monthly_change:+,.0f}".replace(',', '.')
            },
            'historical_x': x.tolist(),
            'historical_y': y.tolist(),
            'fitted_y': y_pred.tolist(),
        }
    
    # =========================================================================
    # Exponential Smoothing
    # =========================================================================
    
    def exponential_smoothing_forecast(self, periods: int = 6, 
                                        alpha: float = 0.3) -> Dict[str, Any]:
        """
        Simple Exponential Smoothing (SES) forecast.
        
        Formula: S_t = α × X_t + (1-α) × S_{t-1}
        - α: smoothing factor (0-1), higher = more weight on recent data
        
        Args:
            periods: Number of periods to forecast
            alpha: Smoothing factor (default 0.3)
            
        Returns:
            Dict with forecast data
        """
        if len(self.monthly_data) < 2:
            return self._empty_forecast("Mindestens 2 Monate Daten erforderlich")
        
        y = self.monthly_data['Amount'].values
        
        # Initialize smoothed values
        smoothed = np.zeros(len(y))
        smoothed[0] = y[0]
        
        # Apply exponential smoothing
        for t in range(1, len(y)):
            smoothed[t] = alpha * y[t] + (1 - alpha) * smoothed[t-1]
        
        # Forecast: use last smoothed value
        last_smoothed = smoothed[-1]
        
        # Calculate trend from smoothed data
        if len(smoothed) >= 3:
            recent_trend = (smoothed[-1] - smoothed[-3]) / 2
        else:
            recent_trend = 0
        
        # Generate forecast with trend adjustment
        last_period = self.monthly_data['Period'].iloc[-1]
        forecast_periods = []
        forecast_values = []
        
        # Calculate standard deviation for confidence
        residuals = y - smoothed
        std_dev = np.std(residuals)
        
        confidence_lower = []
        confidence_upper = []
        
        for i in range(1, periods + 1):
            future_period = last_period + i
            # Damped trend forecast
            forecast_y = last_smoothed + recent_trend * i * 0.8  # Damping factor
            
            forecast_periods.append(str(future_period))
            forecast_values.append(max(0, forecast_y))
            confidence_lower.append(max(0, forecast_y - 1.96 * std_dev * np.sqrt(i)))
            confidence_upper.append(forecast_y + 1.96 * std_dev * np.sqrt(i))
        
        return {
            'method': 'Exponentielle Glättung',
            'periods': forecast_periods,
            'values': forecast_values,
            'confidence_lower': confidence_lower,
            'confidence_upper': confidence_upper,
            'parameters': {
                'alpha': alpha,
                'last_smoothed': last_smoothed,
                'trend': recent_trend,
            },
            'interpretation': {
                'trend': "steigend" if recent_trend > 0 else ("fallend" if recent_trend < 0 else "stabil"),
                'confidence': 1 - (std_dev / np.mean(y)) if np.mean(y) > 0 else 0,
                'message': f"Glättungsfaktor α={alpha}, gewichtete Prognose auf Basis aktueller Entwicklung"
            },
            'smoothed_values': smoothed.tolist(),
        }
    
    # =========================================================================
    # Moving Average Forecast
    # =========================================================================
    
    def moving_average_forecast(self, periods: int = 6, 
                                 window: int = 3) -> Dict[str, Any]:
        """
        Moving Average forecast.
        
        Args:
            periods: Number of periods to forecast
            window: Number of periods for moving average
            
        Returns:
            Dict with forecast data
        """
        if len(self.monthly_data) < window:
            return self._empty_forecast(f"Mindestens {window} Monate Daten erforderlich")
        
        y = self.monthly_data['Amount'].values
        
        # Calculate moving average
        ma = pd.Series(y).rolling(window=window).mean().values
        
        # Last valid moving average
        last_ma = ma[~np.isnan(ma)][-1]
        
        # Trend from moving average
        valid_ma = ma[~np.isnan(ma)]
        if len(valid_ma) >= 2:
            ma_trend = valid_ma[-1] - valid_ma[-2]
        else:
            ma_trend = 0
        
        # Generate forecast
        last_period = self.monthly_data['Period'].iloc[-1]
        forecast_periods = []
        forecast_values = []
        
        std_dev = np.std(y[-window:])
        confidence_lower = []
        confidence_upper = []
        
        for i in range(1, periods + 1):
            future_period = last_period + i
            forecast_y = last_ma + ma_trend * i * 0.5  # Damped trend
            
            forecast_periods.append(str(future_period))
            forecast_values.append(max(0, forecast_y))
            confidence_lower.append(max(0, forecast_y - 1.96 * std_dev))
            confidence_upper.append(forecast_y + 1.96 * std_dev)
        
        return {
            'method': f'Gleitender Durchschnitt ({window}M)',
            'periods': forecast_periods,
            'values': forecast_values,
            'confidence_lower': confidence_lower,
            'confidence_upper': confidence_upper,
            'parameters': {
                'window': window,
                'last_ma': last_ma,
                'trend': ma_trend,
            },
            'interpretation': {
                'trend': "steigend" if ma_trend > 0 else ("fallend" if ma_trend < 0 else "stabil"),
                'confidence': 0.7,  # MA has moderate confidence
                'message': f"Basierend auf Ø der letzten {window} Monate: €{last_ma:,.0f}".replace(',', '.')
            },
            'moving_average': ma.tolist(),
        }
    
    # =========================================================================
    # Seasonal Analysis
    # =========================================================================
    
    def seasonal_analysis(self) -> Dict[str, Any]:
        """
        Analyze seasonal patterns in the data.
        
        Returns:
            Dict with seasonal indices and patterns
        """
        if len(self.monthly_data) < 12:
            return {
                'has_seasonality': False,
                'message': "Mindestens 12 Monate Daten für Saisonanalyse erforderlich",
                'seasonal_indices': {},
                'strong_months': [],
                'weak_months': [],
            }
        
        # Calculate average by month
        monthly_avg = self.monthly_data.groupby('Month')['Amount'].mean()
        overall_avg = self.monthly_data['Amount'].mean()
        
        # Seasonal indices (100 = average)
        seasonal_indices = (monthly_avg / overall_avg * 100).to_dict()
        
        # Identify strong and weak months
        month_names = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
        
        strong_months = []
        weak_months = []
        
        for month, index in seasonal_indices.items():
            month_name = month_names[month - 1]
            if index > 115:
                strong_months.append((month_name, index))
            elif index < 85:
                weak_months.append((month_name, index))
        
        # Calculate seasonality strength
        seasonality_strength = np.std(list(seasonal_indices.values()))
        has_strong_seasonality = seasonality_strength > 15
        
        return {
            'has_seasonality': has_strong_seasonality,
            'seasonality_strength': seasonality_strength,
            'seasonal_indices': seasonal_indices,
            'strong_months': sorted(strong_months, key=lambda x: x[1], reverse=True),
            'weak_months': sorted(weak_months, key=lambda x: x[1]),
            'message': self._seasonal_message(strong_months, weak_months, has_strong_seasonality),
            'monthly_averages': monthly_avg.to_dict(),
        }
    
    def _seasonal_message(self, strong: list, weak: list, has_seasonality: bool) -> str:
        """Generate seasonal analysis message."""
        if not has_seasonality:
            return "Keine signifikante Saisonalität erkannt"
        
        msg_parts = []
        if strong:
            months = ", ".join([m[0] for m in strong[:3]])
            msg_parts.append(f"Starke Monate: {months}")
        if weak:
            months = ", ".join([m[0] for m in weak[:3]])
            msg_parts.append(f"Schwache Monate: {months}")
        
        return " | ".join(msg_parts) if msg_parts else "Saisonale Muster vorhanden"
    
    # =========================================================================
    # Growth Rate Projection
    # =========================================================================
    
    def growth_rate_forecast(self, periods: int = 6) -> Dict[str, Any]:
        """
        Forecast based on historical growth rates.
        
        Formula: F_t = L × (1 + g)^t
        - L: Last known value
        - g: Average growth rate
        
        Args:
            periods: Number of periods to forecast
            
        Returns:
            Dict with forecast data
        """
        if len(self.monthly_data) < 3:
            return self._empty_forecast("Mindestens 3 Monate Daten erforderlich")
        
        y = self.monthly_data['Amount'].values
        
        # Calculate period-over-period growth rates
        growth_rates = []
        for i in range(1, len(y)):
            if y[i-1] > 0:
                rate = (y[i] - y[i-1]) / y[i-1]
                growth_rates.append(rate)
        
        if not growth_rates:
            return self._empty_forecast("Keine Wachstumsraten berechenbar")
        
        # Average growth rate
        avg_growth = np.mean(growth_rates)
        median_growth = np.median(growth_rates)
        std_growth = np.std(growth_rates)
        
        # Use median for more robust forecast
        growth_rate = median_growth
        
        # Last value
        last_value = y[-1]
        
        # Generate forecast
        last_period = self.monthly_data['Period'].iloc[-1]
        forecast_periods = []
        forecast_values = []
        confidence_lower = []
        confidence_upper = []
        
        for i in range(1, periods + 1):
            future_period = last_period + i
            
            # Compound growth
            forecast_y = last_value * ((1 + growth_rate) ** i)
            
            # Confidence based on growth rate variance
            lower = last_value * ((1 + growth_rate - std_growth) ** i)
            upper = last_value * ((1 + growth_rate + std_growth) ** i)
            
            forecast_periods.append(str(future_period))
            forecast_values.append(max(0, forecast_y))
            confidence_lower.append(max(0, lower))
            confidence_upper.append(upper)
        
        # Annual growth projection
        annual_growth = ((1 + growth_rate) ** 12 - 1) * 100
        
        return {
            'method': 'Wachstumsraten-Projektion',
            'periods': forecast_periods,
            'values': forecast_values,
            'confidence_lower': confidence_lower,
            'confidence_upper': confidence_upper,
            'parameters': {
                'monthly_growth_rate': growth_rate,
                'annual_growth_rate': annual_growth / 100,
                'growth_volatility': std_growth,
            },
            'interpretation': {
                'trend': "steigend" if growth_rate > 0.01 else ("fallend" if growth_rate < -0.01 else "stabil"),
                'confidence': max(0, 1 - std_growth),
                'message': f"Ø Monatswachstum: {growth_rate*100:+.1f}%, "
                          f"projiziertes Jahreswachstum: {annual_growth:+.1f}%"
            },
            'growth_rates': growth_rates,
        }
    
    # =========================================================================
    # Combined Forecast
    # =========================================================================
    
    def combined_forecast(self, periods: int = 6) -> Dict[str, Any]:
        """
        Combined forecast using multiple methods with weighted average.
        
        Args:
            periods: Number of periods to forecast
            
        Returns:
            Dict with combined forecast
        """
        forecasts = []
        weights = []
        
        # Linear regression
        lr = self.linear_regression_forecast(periods)
        if lr['values']:
            forecasts.append(('Lineare Regression', lr['values'], lr['parameters'].get('r_squared', 0.5)))
            weights.append(lr['parameters'].get('r_squared', 0.5))
        
        # Exponential smoothing
        es = self.exponential_smoothing_forecast(periods)
        if es['values']:
            forecasts.append(('Exp. Glättung', es['values'], 0.6))
            weights.append(0.6)
        
        # Growth rate
        gr = self.growth_rate_forecast(periods)
        if gr['values']:
            conf = gr['interpretation'].get('confidence', 0.5)
            forecasts.append(('Wachstumsrate', gr['values'], conf))
            weights.append(conf)
        
        if not forecasts:
            return self._empty_forecast("Keine Prognose möglich")
        
        # Weighted average
        total_weight = sum(weights)
        combined_values = []
        
        for i in range(periods):
            weighted_sum = 0
            for (name, values, weight) in forecasts:
                if i < len(values):
                    weighted_sum += values[i] * weight
            combined_values.append(weighted_sum / total_weight if total_weight > 0 else 0)
        
        # Get periods from first forecast
        forecast_periods = forecasts[0][1] if forecasts else []
        if isinstance(lr.get('periods'), list):
            forecast_periods = lr['periods']
        
        return {
            'method': 'Kombinierte Prognose',
            'periods': forecast_periods,
            'values': combined_values,
            'individual_forecasts': {name: values for name, values, _ in forecasts},
            'weights': {name: weight for (name, _, weight), weight in zip(forecasts, weights)},
            'interpretation': {
                'trend': self._determine_trend(combined_values),
                'confidence': np.mean(weights),
                'message': f"Gewichteter Durchschnitt aus {len(forecasts)} Methoden"
            }
        }
    
    def _determine_trend(self, values: list) -> str:
        """Determine trend direction from values."""
        if len(values) < 2:
            return "stabil"
        change = (values[-1] - values[0]) / values[0] if values[0] > 0 else 0
        if change > 0.05:
            return "steigend"
        elif change < -0.05:
            return "fallend"
        return "stabil"
    
    def _empty_forecast(self, message: str) -> Dict[str, Any]:
        """Return empty forecast with message."""
        return {
            'method': 'Keine Prognose',
            'periods': [],
            'values': [],
            'confidence_lower': [],
            'confidence_upper': [],
            'parameters': {},
            'interpretation': {
                'trend': 'unbekannt',
                'confidence': 0,
                'message': message
            }
        }
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics of the data."""
        if self.monthly_data.empty:
            return {}
        
        y = self.monthly_data['Amount'].values
        
        return {
            'count': len(y),
            'total': np.sum(y),
            'mean': np.mean(y),
            'median': np.median(y),
            'std': np.std(y),
            'min': np.min(y),
            'max': np.max(y),
            'cv': np.std(y) / np.mean(y) if np.mean(y) > 0 else 0,  # Coefficient of variation
        }

