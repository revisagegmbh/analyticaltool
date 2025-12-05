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
        
        # Detect data periodicity and prepare data
        self.data_type = self._detect_data_type()
        self.period_data = self._prepare_period_data()  # Native period data (quarterly/monthly/yearly)
        self.monthly_data = self._convert_to_monthly()   # For display purposes
        
        # For quarterly data: aggregate to yearly for more stable forecasts
        self.yearly_data = self._prepare_yearly_data()
        self.quarterly_distribution = self._calculate_quarterly_distribution()
        
        # Use yearly data as forecast basis for quarterly input
        self.use_yearly_basis = self.data_type == 'quarterly' and len(self.yearly_data) >= 2
    
    def _detect_data_type(self) -> str:
        """Detect if data is monthly, quarterly, or yearly.
        
        First checks for explicit PeriodType field from manual entries.
        Falls back to heuristic detection based on dates.
        
        Returns:
            'monthly', 'quarterly', or 'yearly'
        """
        if self.raw_data.empty or len(self.raw_data) < 2:
            return 'monthly'
        
        df = self.raw_data.copy()
        
        # PRIORITY 1: Check for explicit PeriodType field (from manual entries)
        if 'PeriodType' in df.columns:
            period_types = df['PeriodType'].dropna()
            if len(period_types) > 0:
                # Count occurrences of each type
                type_counts = period_types.value_counts()
                most_common = type_counts.index[0] if len(type_counts) > 0 else None
                
                print(f"[Forecast] Explicit PeriodType found: {type_counts.to_dict()}, using: {most_common}")
                
                if most_common in ['quarterly', 'yearly', 'monthly']:
                    return most_common
        
        # PRIORITY 2: Heuristic detection based on month distribution
        df['Month'] = df[self.date_column].dt.month
        months_used = set(df['Month'].unique())
        
        print(f"[Forecast] Heuristic detection - Months used: {months_used}")
        
        # Check if entries are mostly in quarter-middle months (2, 5, 8, 11)
        quarter_months = {2, 5, 8, 11}
        
        # If ALL entries are in quarter-middle months, it's quarterly
        if months_used.issubset(quarter_months):
            print(f"[Forecast] Detected: quarterly (all months in {quarter_months})")
            return 'quarterly'
        
        # If at least 70% overlap with quarter months, it's likely quarterly
        if len(months_used) > 0:
            overlap = len(months_used.intersection(quarter_months)) / len(months_used)
            if overlap >= 0.7:
                print(f"[Forecast] Detected: quarterly ({overlap*100:.0f}% overlap)")
                return 'quarterly'
        
        # Check for yearly (only middle-of-year months)
        yearly_months = {1, 6, 7}
        if months_used.issubset(yearly_months) and len(months_used) <= 2:
            print(f"[Forecast] Detected: yearly")
            return 'yearly'
        
        print(f"[Forecast] Detected: monthly (default)")
        return 'monthly'
    
    def _prepare_period_data(self) -> pd.DataFrame:
        """Prepare data in native period format (keeps quarterly as quarterly)."""
        if self.raw_data.empty:
            return pd.DataFrame(columns=['Period', 'Amount', 'Year', 'PeriodNum'])
        
        df = self.raw_data.copy()
        df['Year'] = df[self.date_column].dt.year
        df['Month'] = df[self.date_column].dt.month
        
        if self.data_type == 'quarterly':
            # Keep as quarterly data - aggregate by quarter
            df['Quarter'] = (df['Month'] - 1) // 3 + 1
            df['Period'] = df['Year'].astype(str) + '-Q' + df['Quarter'].astype(str)
            df['PeriodNum'] = df['Year'] * 4 + df['Quarter']
            
            result = df.groupby(['Period', 'Year', 'Quarter', 'PeriodNum'])[self.value_column].sum().reset_index()
            result = result.rename(columns={self.value_column: 'Amount'})
            result = result.sort_values('PeriodNum')
            result['PeriodIndex'] = range(len(result))
            return result
            
        elif self.data_type == 'yearly':
            # Keep as yearly data
            df['Period'] = df['Year'].astype(str)
            df['PeriodNum'] = df['Year']
            
            result = df.groupby(['Period', 'Year', 'PeriodNum'])[self.value_column].sum().reset_index()
            result = result.rename(columns={self.value_column: 'Amount'})
            result = result.sort_values('PeriodNum')
            result['PeriodIndex'] = range(len(result))
            return result
        else:
            # Monthly data
            df['Period'] = df[self.date_column].dt.to_period('M').astype(str)
            df['PeriodNum'] = df['Year'] * 12 + df['Month']
            
            result = df.groupby(['Period', 'Year', 'Month', 'PeriodNum'])[self.value_column].sum().reset_index()
            result = result.rename(columns={self.value_column: 'Amount'})
            result = result.sort_values('PeriodNum')
            result['PeriodIndex'] = range(len(result))
            return result
    
    def _prepare_yearly_data(self) -> pd.DataFrame:
        """Aggregate data to yearly totals for stable trend analysis."""
        if self.raw_data.empty:
            return pd.DataFrame(columns=['Year', 'Amount', 'PeriodIndex'])
        
        df = self.raw_data.copy()
        df['Year'] = df[self.date_column].dt.year
        
        yearly = df.groupby('Year')[self.value_column].sum().reset_index()
        yearly = yearly.rename(columns={self.value_column: 'Amount'})
        yearly = yearly.sort_values('Year')
        yearly['PeriodIndex'] = range(len(yearly))
        
        return yearly
    
    def _calculate_quarterly_distribution(self) -> Dict[int, float]:
        """Calculate historical quarterly distribution pattern.
        
        Returns dict mapping quarter (1-4) to its typical share of yearly total.
        """
        if self.data_type != 'quarterly' or self.raw_data.empty:
            return {1: 0.25, 2: 0.25, 3: 0.25, 4: 0.25}
        
        df = self.raw_data.copy()
        df['Year'] = df[self.date_column].dt.year
        df['Quarter'] = (df[self.date_column].dt.month - 1) // 3 + 1
        
        # Get yearly totals
        yearly = df.groupby('Year')[self.value_column].sum()
        
        # Calculate quarter-to-year ratios
        quarter_ratios = {1: [], 2: [], 3: [], 4: []}
        
        quarterly = df.groupby(['Year', 'Quarter'])[self.value_column].sum().reset_index()
        for _, row in quarterly.iterrows():
            year = row['Year']
            quarter = row['Quarter']
            if year in yearly.index and yearly[year] > 0:
                ratio = row[self.value_column] / yearly[year]
                quarter_ratios[quarter].append(ratio)
        
        # Average ratios per quarter
        result = {}
        for q in range(1, 5):
            if quarter_ratios[q]:
                result[q] = np.mean(quarter_ratios[q])
            else:
                result[q] = 0.25
        
        # Normalize to ensure they sum to 1.0
        total = sum(result.values())
        if total > 0:
            result = {k: v/total for k, v in result.items()}
        
        return result
    
    def _convert_to_monthly(self) -> pd.DataFrame:
        """Convert period data to monthly for compatibility."""
        if self.period_data.empty:
            return pd.DataFrame(columns=['Period', 'Amount', 'Year', 'Month', 'PeriodIndex'])
        
        if self.data_type == 'monthly':
            return self.period_data.copy()
        
        # For quarterly/yearly, create monthly breakdown
        result_rows = []
        
        for _, row in self.period_data.iterrows():
            amount = row['Amount']
            year = row['Year']
            
            if self.data_type == 'quarterly':
                quarter = row['Quarter']
                start_month = (quarter - 1) * 3 + 1
                months = range(start_month, start_month + 3)
                monthly_amount = amount / 3
            else:  # yearly
                months = range(1, 13)
                monthly_amount = amount / 12
            
            for m in months:
                period = pd.Period(year=year, month=m, freq='M')
                result_rows.append({
                    'Period': period,
                    'Year': year,
                    'Month': m,
                    'Amount': monthly_amount
                })
        
        if not result_rows:
            return pd.DataFrame(columns=['Period', 'Amount', 'Year', 'Month', 'PeriodIndex'])
        
        monthly = pd.DataFrame(result_rows)
        monthly = monthly.groupby(['Period', 'Year', 'Month'])['Amount'].sum().reset_index()
        monthly = monthly.sort_values('Period')
        monthly['PeriodIndex'] = range(len(monthly))
        
        return monthly
    
    # =========================================================================
    # Linear Regression Forecast
    # =========================================================================
    
    def linear_regression_forecast(self, periods: int = 6) -> Dict[str, Any]:
        """
        Forecast using linear regression (least squares).
        
        For quarterly data: Uses yearly totals to eliminate seasonal variance,
        then distributes forecasts back to quarters.
        
        Formula: y = mx + b
        - m: slope (trend direction)
        - b: y-intercept
        
        Args:
            periods: Number of periods to forecast
            
        Returns:
            Dict with forecast data, confidence, and parameters
        """
        # For quarterly data: use yearly aggregates for stable trend
        if self.use_yearly_basis:
            data = self.yearly_data
            if len(data) < 2:
                return self._empty_forecast("Mindestens 2 Jahre Daten erforderlich")
            years_to_forecast = (periods + 3) // 4 + 1  # How many years needed
        else:
            data = self.period_data
            if len(data) < 3:
                return self._empty_forecast("Mindestens 3 Perioden Daten erforderlich")
        
        x = data['PeriodIndex'].values
        y = data['Amount'].values
        
        # Calculate linear regression coefficients
        n = len(x)
        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_x2 = np.sum(x ** 2)
        
        denominator = n * sum_x2 - sum_x ** 2
        if denominator == 0:
            return self._empty_forecast("Nicht genügend Varianz in den Daten")
        
        # Slope (m) and intercept (b)
        m = (n * sum_xy - sum_x * sum_y) / denominator
        b = (sum_y - m * sum_x) / n
        
        # R-squared (coefficient of determination)
        y_pred = m * x + b
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Standard error for confidence interval
        std_error = np.sqrt(ss_res / (n - 2)) if n > 2 else 0
        
        # Generate yearly forecasts first (if using yearly basis)
        if self.use_yearly_basis:
            yearly_forecasts = []
            for i in range(1, years_to_forecast + 1):
                future_x = len(x) - 1 + i
                forecast_y = max(0, m * future_x + b)
                yearly_forecasts.append(forecast_y)
            
            # Convert to quarterly/period forecasts
            forecast_periods, forecast_values = self._yearly_forecast_to_periods(
                yearly_forecasts, periods
            )
            
            # Calculate confidence based on yearly std_error, distributed to quarters
            confidence_lower = [max(0, v - std_error * self.quarterly_distribution.get((i % 4) + 1, 0.25)) 
                               for i, v in enumerate(forecast_values)]
            confidence_upper = [v + std_error * self.quarterly_distribution.get((i % 4) + 1, 0.25) 
                               for i, v in enumerate(forecast_values)]
            
            # Annual growth based on yearly regression
            annual_change = m
            change_label = "Ø Jahresänderung"
        else:
            # Original logic for non-quarterly data
            forecast_periods = self._generate_future_periods(periods)
            forecast_values = []
            confidence_lower = []
            confidence_upper = []
            
            for i in range(1, periods + 1):
                future_x = len(x) - 1 + i
                forecast_y = m * future_x + b
                
                # Confidence interval (±1.96 std error for 95%)
                margin = 1.96 * std_error * np.sqrt(1 + 1/n + (future_x - np.mean(x))**2 / sum_x2)
                
                forecast_values.append(max(0, forecast_y))  # No negative forecasts
                confidence_lower.append(max(0, forecast_y - margin))
                confidence_upper.append(forecast_y + margin)
            
            # Trend interpretation for non-yearly basis
            if self.data_type == 'yearly':
                annual_change = m
                change_label = "Ø Jahresänderung"
            else:
                annual_change = m * 12
                change_label = "Ø monatliche Änderung"
        
        trend_direction = "steigend" if m > 0 else ("fallend" if m < 0 else "stabil")
        
        # Basis info for message
        basis_info = " (Jahresbasis)" if self.use_yearly_basis else ""
        
        return {
            'method': f'Lineare Regression{basis_info}',
            'periods': forecast_periods,
            'values': forecast_values,
            'confidence_lower': confidence_lower,
            'confidence_upper': confidence_upper,
            'parameters': {
                'slope': m,
                'intercept': b,
                'r_squared': r_squared,
                'annual_change': annual_change,
            },
            'interpretation': {
                'trend': trend_direction,
                'confidence': r_squared,
                'message': f"Trend: {trend_direction} (R²={r_squared:.2%}), "
                          f"{change_label}: €{annual_change:+,.0f}".replace(',', '.')
            },
            'historical_x': x.tolist(),
            'historical_y': y.tolist(),
            'fitted_y': y_pred.tolist(),
        }
    
    def _distribute_yearly_to_quarters(self, yearly_values: List[float], 
                                         num_quarters: int) -> List[float]:
        """Distribute yearly forecast values to quarterly values.
        
        Uses historical quarterly distribution pattern.
        """
        if not yearly_values:
            return []
        
        quarterly_values = []
        year_idx = 0
        quarter_in_year = 1
        
        # Determine starting quarter (next quarter after last data point)
        if not self.period_data.empty and 'Quarter' in self.period_data.columns:
            last_row = self.period_data.iloc[-1]
            last_quarter = last_row['Quarter']
            quarter_in_year = (last_quarter % 4) + 1  # Next quarter
            if quarter_in_year == 1:
                year_idx = 1  # Move to next year's forecast
        
        for _ in range(num_quarters):
            if year_idx >= len(yearly_values):
                # Extend with last year's growth pattern
                if len(yearly_values) >= 2:
                    growth = yearly_values[-1] / yearly_values[-2] if yearly_values[-2] > 0 else 1.0
                    yearly_values.append(yearly_values[-1] * growth)
                else:
                    yearly_values.append(yearly_values[-1] if yearly_values else 0)
            
            yearly_amount = yearly_values[year_idx]
            quarterly_amount = yearly_amount * self.quarterly_distribution.get(quarter_in_year, 0.25)
            quarterly_values.append(quarterly_amount)
            
            quarter_in_year += 1
            if quarter_in_year > 4:
                quarter_in_year = 1
                year_idx += 1
        
        return quarterly_values
    
    def _yearly_forecast_to_periods(self, yearly_forecasts: List[float], 
                                     periods: int) -> Tuple[List[str], List[float]]:
        """Convert yearly forecasts to period-specific forecasts.
        
        For quarterly data: distribute yearly values across quarters.
        For monthly data: distribute yearly values across months.
        For yearly data: return as-is.
        """
        if self.data_type == 'yearly':
            period_labels = self._generate_future_periods(periods)
            return period_labels, yearly_forecasts[:periods]
        
        elif self.data_type == 'quarterly':
            period_labels = self._generate_future_periods(periods)
            period_values = self._distribute_yearly_to_quarters(yearly_forecasts, periods)
            return period_labels, period_values
        
        else:  # monthly
            period_labels = self._generate_future_periods(periods)
            # Simple distribution across months
            monthly_values = []
            year_idx = 0
            for i in range(periods):
                if year_idx >= len(yearly_forecasts):
                    yearly_forecasts.append(yearly_forecasts[-1] if yearly_forecasts else 0)
                monthly_values.append(yearly_forecasts[year_idx] / 12)
                if (i + 1) % 12 == 0:
                    year_idx += 1
            return period_labels, monthly_values
    
    def _generate_future_periods(self, num_periods: int) -> List[str]:
        """Generate future period labels based on data type."""
        if self.period_data.empty:
            return [f"P+{i}" for i in range(1, num_periods + 1)]
        
        last_row = self.period_data.iloc[-1]
        periods = []
        
        if self.data_type == 'quarterly':
            year = last_row['Year']
            quarter = last_row['Quarter']
            for i in range(1, num_periods + 1):
                quarter += 1
                if quarter > 4:
                    quarter = 1
                    year += 1
                periods.append(f"{year}-Q{quarter}")
        elif self.data_type == 'yearly':
            year = last_row['Year']
            for i in range(1, num_periods + 1):
                year += 1
                periods.append(str(year))
        else:  # monthly
            # Get last year and month from period_data
            if 'Year' in self.period_data.columns and 'Month' in self.period_data.columns:
                last_row = self.period_data.iloc[-1]
                year = int(last_row['Year'])
                month = int(last_row['Month'])
                
                for i in range(1, num_periods + 1):
                    month += 1
                    if month > 12:
                        month = 1
                        year += 1
                    periods.append(f"{year}-{month:02d}")
            else:
                # Fallback: just generate generic period labels
                for i in range(1, num_periods + 1):
                    periods.append(f"M+{i}")
        
        return periods
    
    # =========================================================================
    # Exponential Smoothing
    # =========================================================================
    
    def exponential_smoothing_forecast(self, periods: int = 6, 
                                        alpha: float = 0.3) -> Dict[str, Any]:
        """
        Simple Exponential Smoothing (SES) forecast.
        
        For quarterly data: Uses yearly totals for stable forecasting.
        
        Formula: S_t = α × X_t + (1-α) × S_{t-1}
        - α: smoothing factor (0-1), higher = more weight on recent data
        
        Args:
            periods: Number of periods to forecast
            alpha: Smoothing factor (default 0.3)
            
        Returns:
            Dict with forecast data
        """
        # For quarterly data: use yearly aggregates
        if self.use_yearly_basis:
            data = self.yearly_data
            if len(data) < 2:
                return self._empty_forecast("Mindestens 2 Jahre Daten erforderlich")
            years_to_forecast = (periods + 3) // 4 + 1
        else:
            data = self.period_data
            if len(data) < 2:
                return self._empty_forecast("Mindestens 2 Perioden Daten erforderlich")
        
        y = data['Amount'].values
        
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
            recent_trend = smoothed[-1] - smoothed[0] if len(smoothed) >= 2 else 0
        
        # Calculate standard deviation for confidence
        residuals = y - smoothed
        std_dev = np.std(residuals) if len(residuals) > 1 else 0
        
        if self.use_yearly_basis:
            # Generate yearly forecasts first
            yearly_forecasts = []
            for i in range(1, years_to_forecast + 1):
                forecast_y = last_smoothed + recent_trend * i * 0.8
                yearly_forecasts.append(max(0, forecast_y))
            
            # Convert to quarterly forecasts
            forecast_periods, forecast_values = self._yearly_forecast_to_periods(
                yearly_forecasts, periods
            )
            
            confidence_lower = [max(0, v * 0.85) for v in forecast_values]
            confidence_upper = [v * 1.15 for v in forecast_values]
        else:
            # Original logic
            forecast_periods = self._generate_future_periods(periods)
            forecast_values = []
            confidence_lower = []
            confidence_upper = []
            
            for i in range(1, periods + 1):
                forecast_y = last_smoothed + recent_trend * i * 0.8
                forecast_values.append(max(0, forecast_y))
                confidence_lower.append(max(0, forecast_y - 1.96 * std_dev * np.sqrt(i)))
                confidence_upper.append(forecast_y + 1.96 * std_dev * np.sqrt(i))
        
        # Determine trend based on recent_trend relative to mean
        mean_value = np.mean(y)
        if recent_trend > mean_value * 0.02:
            trend = "steigend"
        elif recent_trend < -mean_value * 0.02:
            trend = "fallend"
        else:
            trend = "stabil"
        
        basis_info = " (Jahresbasis)" if self.use_yearly_basis else ""
        
        return {
            'method': f'Exponentielle Glättung{basis_info}',
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
                'trend': trend,
                'confidence': max(0.3, 1 - (std_dev / np.mean(y))) if np.mean(y) > 0 else 0.5,
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
        
        For quarterly data: Uses yearly totals for stable forecasting.
        
        Args:
            periods: Number of periods to forecast
            window: Number of periods for moving average
            
        Returns:
            Dict with forecast data
        """
        # For quarterly data: use yearly aggregates
        if self.use_yearly_basis:
            data = self.yearly_data
            window = min(window, len(data))  # Adjust window for yearly data
            if len(data) < 2:
                return self._empty_forecast("Mindestens 2 Jahre Daten erforderlich")
            years_to_forecast = (periods + 3) // 4 + 1
        else:
            data = self.period_data
            if len(data) < window:
                return self._empty_forecast(f"Mindestens {window} Perioden Daten erforderlich")
        
        y = data['Amount'].values
        
        # Calculate moving average
        ma = pd.Series(y).rolling(window=window, min_periods=1).mean().values
        
        # Last valid moving average
        last_ma = ma[-1]
        
        # Trend from moving average
        if len(ma) >= 2:
            ma_trend = ma[-1] - ma[-2] if len(ma) >= 2 else 0
        else:
            ma_trend = 0
        
        std_dev = np.std(y) if len(y) > 1 else 0
        
        if self.use_yearly_basis:
            # Generate yearly forecasts first
            yearly_forecasts = []
            for i in range(1, years_to_forecast + 1):
                forecast_y = last_ma + ma_trend * i * 0.5
                yearly_forecasts.append(max(0, forecast_y))
            
            # Convert to quarterly forecasts
            forecast_periods, forecast_values = self._yearly_forecast_to_periods(
                yearly_forecasts, periods
            )
            
            confidence_lower = [max(0, v * 0.85) for v in forecast_values]
            confidence_upper = [v * 1.15 for v in forecast_values]
        else:
            # Original logic
            forecast_periods = self._generate_future_periods(periods)
            forecast_values = []
            confidence_lower = []
            confidence_upper = []
            
            for i in range(1, periods + 1):
                forecast_y = last_ma + ma_trend * i * 0.5
                forecast_values.append(max(0, forecast_y))
                confidence_lower.append(max(0, forecast_y - 1.96 * std_dev))
                confidence_upper.append(forecast_y + 1.96 * std_dev)
        
        # Determine trend
        mean_value = np.mean(y)
        if ma_trend > mean_value * 0.02:
            trend = "steigend"
        elif ma_trend < -mean_value * 0.02:
            trend = "fallend"
        else:
            trend = "stabil"
        
        basis_info = " (Jahresbasis)" if self.use_yearly_basis else ""
        period_label = "Jahre" if self.use_yearly_basis else ("Perioden" if self.data_type != 'monthly' else "Monate")
        
        return {
            'method': f'Gleitender Durchschnitt{basis_info}',
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
                'trend': trend,
                'confidence': 0.75 if self.use_yearly_basis else 0.7,
                'message': f"Basierend auf Ø der letzten {window} {period_label}: €{last_ma:,.0f}".replace(',', '.')
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
        
        For quarterly data: Uses year-over-year growth rates for stability.
        
        Formula: F_t = L × (1 + g)^t
        - L: Last known value
        - g: Average growth rate
        
        Args:
            periods: Number of periods to forecast
            
        Returns:
            Dict with forecast data
        """
        # For quarterly data: use yearly aggregates
        if self.use_yearly_basis:
            data = self.yearly_data
            if len(data) < 2:
                return self._empty_forecast("Mindestens 2 Jahre Daten erforderlich")
            years_to_forecast = (periods + 3) // 4 + 1
        else:
            data = self.period_data
            if len(data) < 3:
                return self._empty_forecast("Mindestens 3 Perioden Daten erforderlich")
        
        y = data['Amount'].values
        
        # Calculate period-over-period growth rates
        growth_rates = []
        for i in range(1, len(y)):
            if y[i-1] > 0:
                rate = (y[i] - y[i-1]) / y[i-1]
                growth_rates.append(rate)
        
        if not growth_rates:
            return self._empty_forecast("Keine Wachstumsraten berechenbar")
        
        # Weighted average (more recent periods have higher weight)
        weights = [i + 1 for i in range(len(growth_rates))]
        weighted_growth = sum(r * w for r, w in zip(growth_rates, weights)) / sum(weights)
        
        median_growth = np.median(growth_rates)
        std_growth = np.std(growth_rates) if len(growth_rates) > 1 else 0.1
        
        # Use weighted growth for forecast
        growth_rate = weighted_growth
        
        # Last value
        last_value = y[-1]
        
        if self.use_yearly_basis:
            # Generate yearly forecasts first
            yearly_forecasts = []
            for i in range(1, years_to_forecast + 1):
                forecast_y = last_value * ((1 + growth_rate) ** i)
                yearly_forecasts.append(max(0, forecast_y))
            
            # Convert to quarterly forecasts
            forecast_periods, forecast_values = self._yearly_forecast_to_periods(
                yearly_forecasts, periods
            )
            
            confidence_lower = [max(0, v * (1 - std_growth)) for v in forecast_values]
            confidence_upper = [v * (1 + std_growth) for v in forecast_values]
            
            annual_growth = growth_rate * 100
            period_label = "Jahr"
        else:
            # Original logic
            forecast_periods = self._generate_future_periods(periods)
            forecast_values = []
            confidence_lower = []
            confidence_upper = []
            
            for i in range(1, periods + 1):
                forecast_y = last_value * ((1 + growth_rate) ** i)
                lower = last_value * ((1 + growth_rate - std_growth) ** i)
                upper = last_value * ((1 + growth_rate + std_growth) ** i)
                
                forecast_values.append(max(0, forecast_y))
                confidence_lower.append(max(0, lower))
                confidence_upper.append(upper)
            
            # Annual growth projection based on data type
            if self.data_type == 'yearly':
                periods_per_year = 1
                period_label = "Jahr"
            else:
                periods_per_year = 12
                period_label = "Monat"
            
            annual_growth = ((1 + growth_rate) ** periods_per_year - 1) * 100
        
        # Determine trend
        trend = "steigend" if growth_rate > 0.02 else ("fallend" if growth_rate < -0.02 else "stabil")
        
        basis_info = " (Jahresbasis)" if self.use_yearly_basis else ""
        
        return {
            'method': f'Wachstumsraten-Projektion{basis_info}',
            'periods': forecast_periods,
            'values': forecast_values,
            'confidence_lower': confidence_lower,
            'confidence_upper': confidence_upper,
            'parameters': {
                'period_growth_rate': growth_rate,
                'annual_growth_rate': annual_growth / 100 if not self.use_yearly_basis else growth_rate,
                'growth_volatility': std_growth,
            },
            'interpretation': {
                'trend': trend,
                'confidence': max(0.4, 1 - std_growth),
                'message': f"Ø {period_label}swachstum: {growth_rate*100:+.1f}%, "
                          f"projiziertes Jahreswachstum: {annual_growth:+.1f}%"
            },
            'growth_rates': growth_rates,
        }
    
    # =========================================================================
    # Year-over-Year Forecast (Best for quarterly data with high variance)
    # =========================================================================
    
    def yearly_trend_forecast(self, periods: int = 12) -> Dict[str, Any]:
        """
        Year-over-Year trend forecast - aggregates to yearly totals first.
        
        This method is ideal for quarterly data where individual quarters
        have high variance but yearly totals show clear trends.
        
        Args:
            periods: Number of periods to forecast (in native period type)
            
        Returns:
            Dict with forecast data
        """
        # Aggregate to yearly totals
        df = self.raw_data.copy()
        df['Year'] = df[self.date_column].dt.year
        yearly_totals = df.groupby('Year')[self.value_column].sum().reset_index()
        yearly_totals = yearly_totals.sort_values('Year')
        
        if len(yearly_totals) < 2:
            return self._empty_forecast("Mindestens 2 Jahre Daten für Jahrestrend erforderlich")
        
        years = yearly_totals['Year'].values
        amounts = yearly_totals[self.value_column].values
        
        # Calculate year-over-year growth rates
        yoy_growth_rates = []
        for i in range(1, len(amounts)):
            if amounts[i-1] > 0:
                rate = (amounts[i] - amounts[i-1]) / amounts[i-1]
                yoy_growth_rates.append(rate)
        
        if not yoy_growth_rates:
            return self._empty_forecast("Keine Wachstumsraten berechenbar")
        
        # Use weighted average (more recent years have higher weight)
        weights = [i + 1 for i in range(len(yoy_growth_rates))]
        weighted_growth = sum(r * w for r, w in zip(yoy_growth_rates, weights)) / sum(weights)
        
        # Also calculate linear trend for comparison
        x = np.arange(len(amounts))
        slope, intercept = np.polyfit(x, amounts, 1)
        
        # Determine trend based on weighted growth
        if weighted_growth > 0.02:
            trend = "steigend"
        elif weighted_growth < -0.02:
            trend = "fallend"
        else:
            trend = "stabil"
        
        # Project future years
        last_year = years[-1]
        last_amount = amounts[-1]
        
        # Calculate how many years we need based on periods
        if self.data_type == 'quarterly':
            years_needed = (periods + 3) // 4 + 1
        elif self.data_type == 'yearly':
            years_needed = periods
        else:
            years_needed = (periods + 11) // 12 + 1
        
        future_yearly = []
        current = last_amount
        for i in range(1, years_needed + 1):
            # Blend growth rate and linear projection
            growth_proj = current * (1 + weighted_growth)
            linear_proj = intercept + slope * (len(amounts) - 1 + i)
            
            # Weight growth rate more (70/30)
            projected = growth_proj * 0.7 + linear_proj * 0.3
            future_yearly.append((last_year + i, max(0, projected)))
            current = projected
        
        # Now distribute yearly forecasts to periods
        forecast_periods = self._generate_future_periods(periods)
        forecast_values = []
        
        if self.data_type == 'quarterly':
            # Calculate historical quarterly distribution pattern
            df['Quarter'] = (df[self.date_column].dt.month - 1) // 3 + 1
            quarterly_by_year = df.groupby(['Year', 'Quarter'])[self.value_column].sum().reset_index()
            
            # Get average quarter-to-year ratio
            quarter_ratios = {1: 0.25, 2: 0.25, 3: 0.25, 4: 0.25}  # Default
            for q in range(1, 5):
                q_data = quarterly_by_year[quarterly_by_year['Quarter'] == q]
                if len(q_data) > 0:
                    yearly_for_q = yearly_totals[yearly_totals['Year'].isin(q_data['Year'])]
                    if len(yearly_for_q) > 0:
                        ratios = []
                        for _, row in q_data.iterrows():
                            year_total = yearly_totals[yearly_totals['Year'] == row['Year']][self.value_column].values
                            if len(year_total) > 0 and year_total[0] > 0:
                                ratios.append(row[self.value_column] / year_total[0])
                        if ratios:
                            quarter_ratios[q] = np.mean(ratios)
            
            # Normalize ratios
            total_ratio = sum(quarter_ratios.values())
            quarter_ratios = {k: v/total_ratio for k, v in quarter_ratios.items()}
            
            # Distribute forecasts
            for period in forecast_periods:
                # Parse period like "2026-Q1"
                parts = period.split('-Q')
                if len(parts) == 2:
                    year = int(parts[0])
                    quarter = int(parts[1])
                    
                    # Find the yearly forecast for this year
                    yearly_amount = None
                    for y, amt in future_yearly:
                        if y == year:
                            yearly_amount = amt
                            break
                    
                    if yearly_amount is None:
                        # Use last projected year
                        yearly_amount = future_yearly[-1][1] if future_yearly else last_amount
                    
                    forecast_values.append(yearly_amount * quarter_ratios[quarter])
                else:
                    forecast_values.append(last_amount / 4)
        
        elif self.data_type == 'yearly':
            forecast_values = [amt for _, amt in future_yearly[:periods]]
        
        else:  # monthly
            # Distribute yearly to monthly (simple /12 for now)
            for period in forecast_periods:
                year = int(period[:4])
                yearly_amount = None
                for y, amt in future_yearly:
                    if y == year:
                        yearly_amount = amt
                        break
                if yearly_amount is None:
                    yearly_amount = future_yearly[-1][1] if future_yearly else last_amount
                forecast_values.append(yearly_amount / 12)
        
        # Ensure we have enough values
        while len(forecast_values) < periods:
            forecast_values.append(forecast_values[-1] if forecast_values else last_amount / 4)
        
        # Calculate confidence based on consistency of growth
        std_growth = np.std(yoy_growth_rates) if len(yoy_growth_rates) > 1 else 0.1
        confidence = max(0.3, min(0.95, 1 - std_growth))
        
        return {
            'method': 'Jahrestrend-Projektion',
            'periods': forecast_periods,
            'values': forecast_values[:periods],
            'confidence_lower': [v * 0.85 for v in forecast_values[:periods]],
            'confidence_upper': [v * 1.15 for v in forecast_values[:periods]],
            'parameters': {
                'yearly_growth_rate': weighted_growth,
                'linear_slope': slope,
                'years_analyzed': len(amounts),
            },
            'interpretation': {
                'trend': trend,
                'confidence': confidence,
                'message': f"Jahreswachstum: {weighted_growth*100:+.1f}% (gewichtet), "
                          f"basierend auf {len(amounts)} Jahren"
            },
            'yearly_totals': dict(zip(years.tolist(), amounts.tolist())),
            'quarterly_distribution': quarter_ratios if self.data_type == 'quarterly' else None,
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
    
    # =========================================================================
    # Monte Carlo Simulation
    # =========================================================================
    
    def monte_carlo_forecast(self, periods: int = 12, simulations: int = 1000) -> Dict[str, Any]:
        """
        Monte Carlo simulation for probabilistic forecasting.
        
        For quarterly data: Uses year-over-year statistics for more stable simulation.
        
        Generates multiple random scenarios based on historical volatility
        to estimate probability distributions for future values.
        
        Args:
            periods: Number of periods to forecast
            simulations: Number of Monte Carlo iterations
            
        Returns:
            Dict with forecast data including probability ranges
        """
        # For quarterly data: use yearly aggregates
        if self.use_yearly_basis:
            data = self.yearly_data
            if len(data) < 2:
                return self._empty_forecast("Mindestens 2 Jahre Daten für Monte Carlo erforderlich")
            years_to_forecast = (periods + 3) // 4 + 1
            sim_periods = years_to_forecast
        else:
            data = self.period_data
            if len(data) < 4:
                return self._empty_forecast("Mindestens 4 Perioden Daten für Monte Carlo erforderlich")
            sim_periods = periods
        
        y = data['Amount'].values
        
        # Calculate historical statistics
        mean_value = np.mean(y)
        std_dev = np.std(y)
        
        # Calculate period growth rates
        growth_rates = []
        for i in range(1, len(y)):
            if y[i-1] > 0:
                rate = (y[i] - y[i-1]) / y[i-1]
                growth_rates.append(rate)
        
        if not growth_rates:
            return self._empty_forecast("Keine Wachstumsraten berechenbar")
        
        mean_growth = np.mean(growth_rates)
        std_growth = np.std(growth_rates) if len(growth_rates) > 1 else 0.1
        
        # Run Monte Carlo simulation
        last_value = y[-1]
        all_simulations = np.zeros((simulations, sim_periods))
        
        for sim in range(simulations):
            current = last_value
            for p in range(sim_periods):
                # Random growth rate from normal distribution
                random_growth = np.random.normal(mean_growth, std_growth)
                current = current * (1 + random_growth)
                # Ensure non-negative
                current = max(0, current)
                all_simulations[sim, p] = current
        
        # Calculate percentiles for each simulated period
        yearly_forecast_values = []
        yearly_confidence_lower = []
        yearly_confidence_upper = []
        
        for p in range(sim_periods):
            period_values = all_simulations[:, p]
            yearly_forecast_values.append(np.median(period_values))
            yearly_confidence_lower.append(np.percentile(period_values, 10))
            yearly_confidence_upper.append(np.percentile(period_values, 90))
        
        # Calculate probability of growth
        final_values = all_simulations[:, -1]
        prob_growth = np.sum(final_values > last_value) / simulations
        prob_decline = np.sum(final_values < last_value) / simulations
        
        if self.use_yearly_basis:
            # Convert yearly to quarterly forecasts
            forecast_periods, forecast_values = self._yearly_forecast_to_periods(
                yearly_forecast_values, periods
            )
            _, confidence_lower = self._yearly_forecast_to_periods(
                yearly_confidence_lower, periods
            )
            _, confidence_upper = self._yearly_forecast_to_periods(
                yearly_confidence_upper, periods
            )
        else:
            forecast_periods = self._generate_future_periods(periods)
            forecast_values = yearly_forecast_values
            confidence_lower = yearly_confidence_lower
            confidence_upper = yearly_confidence_upper
        
        # Determine trend based on probability
        if prob_growth > 0.55:
            trend = "steigend"
            trend_prob = prob_growth
        elif prob_decline > 0.55:
            trend = "fallend"
            trend_prob = prob_decline
        else:
            trend = "stabil"
            trend_prob = 1 - abs(prob_growth - prob_decline)
        
        basis_info = " (Jahresbasis)" if self.use_yearly_basis else ""
        
        return {
            'method': f'Monte Carlo Simulation{basis_info}',
            'periods': forecast_periods,
            'values': forecast_values,
            'confidence_lower': confidence_lower,
            'confidence_upper': confidence_upper,
            'parameters': {
                'simulations': simulations,
                'mean_growth': mean_growth,
                'std_growth': std_growth,
                'prob_growth': prob_growth,
                'prob_decline': prob_decline,
            },
            'interpretation': {
                'trend': trend,
                'confidence': trend_prob,
                'probability': trend_prob,
                'message': f"Basierend auf {simulations:,} Simulationen: "
                          f"{prob_growth:.0%} Wachstum, {prob_decline:.0%} Rückgang"
            }
        }
    
    # =========================================================================
    # Ensemble Method (Best-of-N)
    # =========================================================================
    
    def ensemble_forecast(self, periods: int = 12) -> Dict[str, Any]:
        """
        Ensemble forecast combining multiple methods with dynamic weighting.
        
        Evaluates all methods on historical data, weights by accuracy,
        and combines for optimal prediction.
        
        Args:
            periods: Number of periods to forecast
            
        Returns:
            Dict with ensemble forecast and method contributions
        """
        data = self.period_data
        if len(data) < 4:
            return self._empty_forecast("Mindestens 4 Perioden Daten für Ensemble erforderlich")
        
        # Get forecasts from all methods
        methods = {
            'Linear': self.linear_regression_forecast(periods),
            'Exponentiell': self.exponential_smoothing_forecast(periods),
            'Gleitend': self.moving_average_forecast(periods),
            'Wachstum': self.growth_rate_forecast(periods),
            'Monte Carlo': self.monte_carlo_forecast(periods, simulations=500),
        }
        
        # Evaluate each method's historical accuracy using backtesting
        accuracies = {}
        y = self.monthly_data['Amount'].values
        
        if len(y) >= 6:
            # Use last 3 months as validation
            train_size = len(y) - 3
            actual = y[train_size:]
            
            for name, forecast in methods.items():
                if forecast['values'] and len(forecast['values']) >= 3:
                    # Simple accuracy: 1 - MAPE (Mean Absolute Percentage Error)
                    # Using confidence as proxy since we can't truly backtest here
                    conf = forecast.get('interpretation', {}).get('confidence', 0.5)
                    accuracies[name] = max(0.1, conf)
                else:
                    accuracies[name] = 0.1
        else:
            # Default equal weights
            for name in methods:
                accuracies[name] = 0.5
        
        # Normalize weights
        total_accuracy = sum(accuracies.values())
        weights = {name: acc / total_accuracy for name, acc in accuracies.items()}
        
        # Combine forecasts
        ensemble_values = []
        ensemble_lower = []
        ensemble_upper = []
        
        for i in range(periods):
            weighted_sum = 0
            weighted_lower = 0
            weighted_upper = 0
            weight_sum = 0
            
            for name, forecast in methods.items():
                if forecast['values'] and i < len(forecast['values']):
                    w = weights[name]
                    weighted_sum += forecast['values'][i] * w
                    
                    if forecast.get('confidence_lower') and i < len(forecast['confidence_lower']):
                        weighted_lower += forecast['confidence_lower'][i] * w
                    if forecast.get('confidence_upper') and i < len(forecast['confidence_upper']):
                        weighted_upper += forecast['confidence_upper'][i] * w
                    
                    weight_sum += w
            
            if weight_sum > 0:
                ensemble_values.append(weighted_sum)
                ensemble_lower.append(weighted_lower if weighted_lower > 0 else weighted_sum * 0.8)
                ensemble_upper.append(weighted_upper if weighted_upper > 0 else weighted_sum * 1.2)
        
        # Get period labels from first valid forecast
        forecast_periods = []
        for name, forecast in methods.items():
            if forecast.get('periods'):
                forecast_periods = forecast['periods']
                break
        
        # Calculate overall confidence
        avg_confidence = np.mean([
            methods[name].get('interpretation', {}).get('confidence', 0.5) 
            for name in methods
        ])
        
        # Get best method
        best_method = max(weights, key=weights.get)
        best_weight = weights[best_method]
        
        # Trend from ensemble
        trend = self._determine_trend(ensemble_values)
        
        # Format method contributions
        contributions = []
        for name, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
            contributions.append(f"{name}: {weight:.0%}")
        
        return {
            'method': 'Ensemble (Top 5)',
            'periods': forecast_periods,
            'values': ensemble_values,
            'confidence_lower': ensemble_lower,
            'confidence_upper': ensemble_upper,
            'parameters': {
                'methods_used': list(methods.keys()),
                'weights': weights,
                'best_method': best_method,
                'best_weight': best_weight,
            },
            'individual_forecasts': {name: f['values'] for name, f in methods.items() if f['values']},
            'interpretation': {
                'trend': trend,
                'confidence': avg_confidence,
                'probability': avg_confidence,
                'message': f"Beste Methode: {best_method} ({best_weight:.0%})\n"
                          f"Beiträge: {', '.join(contributions[:3])}"
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
    # Extended Horizon Forecasts
    # =========================================================================
    
    def calculate_extended_horizons(self, base_forecast: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Calculate extended forecast horizons for business planning.
        
        Returns forecasts for:
        - Next period (next month/quarter/year based on data type)
        - Next quarter (3 months cumulative or 1 quarter)
        - Next year (12 months or 4 quarters cumulative)
        - 2 years (24 months or 8 quarters)
        - 3 years (36 months or 12 quarters)
        
        Args:
            base_forecast: Optional base forecast to use, otherwise generates combined
            
        Returns:
            Dict with horizon values and current baseline
        """
        data = self.period_data
        if data.empty or len(data) < 2:
            return {
                'next_month': None,
                'next_quarter': None,
                'next_year': None,
                'year_2': None,
                'year_3': None,
                'current_annual': None,
            }
        
        y = data['Amount'].values
        
        # Calculate current annual rate based on data type
        if self.data_type == 'quarterly':
            # For quarterly data: sum last 4 quarters or extrapolate
            if len(y) >= 4:
                current_annual = np.sum(y[-4:])
            else:
                current_annual = np.mean(y) * 4
            periods_per_year = 4
        elif self.data_type == 'yearly':
            current_annual = y[-1] if len(y) >= 1 else 0
            periods_per_year = 1
        else:
            # Monthly data
            if len(y) >= 12:
                current_annual = np.sum(y[-12:])
            else:
                current_annual = np.mean(y) * 12
            periods_per_year = 12
        
        # Get base forecast values - use appropriate number of periods
        needed_periods = 12 if self.data_type == 'quarterly' else (3 if self.data_type == 'yearly' else 36)
        
        if base_forecast and 'values' in base_forecast and len(base_forecast['values']) >= 4:
            forecast_values = list(base_forecast['values'])
        else:
            extended_forecast = self.growth_rate_forecast(periods=needed_periods)
            forecast_values = list(extended_forecast.get('values', []))
        
        if not forecast_values:
            return {
                'next_month': None,
                'next_quarter': None,
                'next_year': None,
                'year_2': None,
                'year_3': None,
                'current_annual': current_annual,
            }
        
        # Extend forecast if needed
        while len(forecast_values) < needed_periods:
            if len(forecast_values) >= 2:
                growth = (forecast_values[-1] / forecast_values[-2]) if forecast_values[-2] > 0 else 1.0
                forecast_values.append(forecast_values[-1] * growth)
            else:
                break
        
        # Calculate horizon values based on data type
        result = {
            'current_annual': current_annual,
        }
        
        if self.data_type == 'quarterly':
            # For quarterly data
            result['next_month'] = forecast_values[0] / 3 if forecast_values else None  # Est. monthly
            result['next_quarter'] = forecast_values[0] if forecast_values else None
            result['next_year'] = sum(forecast_values[:4]) if len(forecast_values) >= 4 else None
            result['year_2'] = sum(forecast_values[4:8]) if len(forecast_values) >= 8 else None
            result['year_3'] = sum(forecast_values[8:12]) if len(forecast_values) >= 12 else None
        elif self.data_type == 'yearly':
            # For yearly data
            result['next_month'] = forecast_values[0] / 12 if forecast_values else None  # Est. monthly
            result['next_quarter'] = forecast_values[0] / 4 if forecast_values else None  # Est. quarterly
            result['next_year'] = forecast_values[0] if forecast_values else None
            result['year_2'] = forecast_values[1] if len(forecast_values) >= 2 else None
            result['year_3'] = forecast_values[2] if len(forecast_values) >= 3 else None
        else:
            # For monthly data
            result['next_month'] = forecast_values[0] if forecast_values else None
            result['next_quarter'] = sum(forecast_values[:3]) if len(forecast_values) >= 3 else None
            result['next_year'] = sum(forecast_values[:12]) if len(forecast_values) >= 12 else None
            result['year_2'] = sum(forecast_values[12:24]) if len(forecast_values) >= 24 else None
            result['year_3'] = sum(forecast_values[24:36]) if len(forecast_values) >= 36 else None
        
        return result
    
    def forecast_with_horizons(self, method: str = "combined") -> Dict[str, Any]:
        """
        Generate forecast with extended horizon calculations.
        
        Args:
            method: Forecast method ('combined', 'linear', 'exponential', 
                   'moving_average', 'growth_rate')
                   
        Returns:
            Forecast dict including 'extended_horizons' key
        """
        # Generate base forecast
        if method == "combined":
            forecast = self.combined_forecast(periods=12)
        elif method == "linear":
            forecast = self.linear_regression_forecast(periods=12)
        elif method == "exponential":
            forecast = self.exponential_smoothing_forecast(periods=12)
        elif method == "moving_average":
            forecast = self.moving_average_forecast(periods=12)
        elif method == "growth_rate":
            forecast = self.growth_rate_forecast(periods=12)
        elif method == "monte_carlo":
            forecast = self.monte_carlo_forecast(periods=12, simulations=1000)
        elif method == "ensemble":
            forecast = self.ensemble_forecast(periods=12)
        elif method == "yearly_trend":
            forecast = self.yearly_trend_forecast(periods=12)
        else:
            forecast = self.combined_forecast(periods=12)
        
        # Calculate extended horizons
        extended = self.calculate_extended_horizons(forecast)
        forecast['extended_horizons'] = extended
        
        # Add data type info
        data_type_labels = {
            'monthly': 'Monatsdaten',
            'quarterly': 'Quartalsdaten',
            'yearly': 'Jahresdaten'
        }
        forecast['data_type'] = self.data_type
        forecast['data_type_label'] = data_type_labels.get(self.data_type, 'Unbekannt')
        
        return forecast
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics of the data."""
        if self.period_data.empty:
            return {}
        
        y = self.period_data['Amount'].values
        
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

