"""
Recommendation Engine - Rule-Based Business Insights
100% deterministic, no AI/LLM - pure mathematical rules

Categories:
- Profit & Margin Analysis
- Trend Analysis
- Seasonal Insights
- Efficiency Recommendations
- Risk Alerts
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import numpy as np
import pandas as pd


class Severity(Enum):
    """Recommendation severity levels."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Category(Enum):
    """Recommendation categories."""
    TREND = "trend"
    SEASONAL = "seasonal"
    EFFICIENCY = "efficiency"
    RISK = "risk"
    OPPORTUNITY = "opportunity"
    PROFIT = "profit"


@dataclass
class Recommendation:
    """A single recommendation."""
    id: str
    category: Category
    severity: Severity
    title: str
    message: str
    action: str
    data_basis: Dict[str, Any]
    confidence: float  # 0-1
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'category': self.category.value,
            'severity': self.severity.value,
            'title': self.title,
            'message': self.message,
            'action': self.action,
            'data_basis': self.data_basis,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
        }


class RecommendationEngine:
    """
    Rule-based recommendation engine.
    Analyzes data and generates actionable insights.
    """
    
    # Configurable thresholds
    THRESHOLDS = {
        # Trend thresholds
        'declining_trend_pct': -5.0,      # % decline triggers warning
        'strong_growth_pct': 15.0,        # % growth = opportunity
        
        # Volatility thresholds
        'high_volatility_cv': 0.3,        # Coefficient of variation
        
        # Seasonal thresholds
        'seasonal_strength': 15.0,        # Standard deviation of seasonal indices
        
        # Growth thresholds
        'yoy_decline_warning': -10.0,     # YoY decline warning
        'yoy_growth_opportunity': 20.0,   # YoY growth opportunity
        
        # Concentration thresholds
        'high_concentration': 0.5,        # Single month > 50% of total
    }
    
    def __init__(self, revenue_data: pd.DataFrame = None,
                 expense_data: pd.DataFrame = None,
                 marketing_data: pd.DataFrame = None):
        """
        Initialize recommendation engine.
        
        Args:
            revenue_data: Revenue DataFrame
            expense_data: Expense DataFrame (optional)
            marketing_data: Marketing DataFrame (optional)
        """
        self.revenue_data = revenue_data if revenue_data is not None else pd.DataFrame()
        self.expense_data = expense_data if expense_data is not None else pd.DataFrame()
        self.marketing_data = marketing_data if marketing_data is not None else pd.DataFrame()
        
        self.recommendations: List[Recommendation] = []
    
    def analyze_all(self) -> List[Recommendation]:
        """
        Run all analysis rules and generate recommendations.
        
        Returns:
            List of Recommendation objects
        """
        self.recommendations = []
        
        if not self.revenue_data.empty:
            self._analyze_revenue_trends()
            self._analyze_seasonality()
            self._analyze_volatility()
            self._analyze_concentration()
            self._analyze_growth()
            self._analyze_opportunities()
        
        # Sort by severity (critical first)
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4,
        }
        self.recommendations.sort(key=lambda r: severity_order[r.severity])
        
        return self.recommendations
    
    # =========================================================================
    # Trend Analysis Rules
    # =========================================================================
    
    def _analyze_revenue_trends(self):
        """Analyze revenue trends and generate recommendations."""
        if len(self.revenue_data) < 6:
            return
        
        df = self.revenue_data.copy()
        df['YearMonth'] = df['Date'].dt.to_period('M')
        monthly = df.groupby('YearMonth')['Amount'].sum().reset_index()
        monthly['Amount'] = monthly['Amount'].astype(float)
        
        if len(monthly) < 3:
            return
        
        # Calculate trend (linear regression slope)
        x = np.arange(len(monthly))
        y = monthly['Amount'].values
        
        # Simple linear regression
        slope = np.polyfit(x, y, 1)[0]
        avg_value = np.mean(y)
        trend_pct = (slope / avg_value) * 100 if avg_value > 0 else 0
        
        # Recent trend (last 3 months)
        if len(y) >= 3:
            recent_slope = (y[-1] - y[-3]) / 2
            recent_trend_pct = (recent_slope / avg_value) * 100 if avg_value > 0 else 0
        else:
            recent_trend_pct = trend_pct
        
        # Declining trend warning
        if trend_pct < self.THRESHOLDS['declining_trend_pct']:
            self.recommendations.append(Recommendation(
                id='trend_decline',
                category=Category.TREND,
                severity=Severity.HIGH,
                title='Negativer Trend erkannt',
                message=f'Die Einnahmen zeigen einen Abwärtstrend von {trend_pct:.1f}% pro Monat. '
                       f'Bei Fortsetzung könnten die Einnahmen in 6 Monaten um €{abs(slope*6):,.0f} sinken.'.replace(',', '.'),
                action='Ursachenanalyse durchführen und Gegenmaßnahmen einleiten',
                data_basis={'trend_pct': trend_pct, 'slope': slope, 'months_analyzed': len(monthly)},
                confidence=min(0.9, len(monthly) / 12)  # More data = higher confidence
            ))
        
        # Accelerating decline (recent worse than overall)
        elif recent_trend_pct < trend_pct - 5:
            self.recommendations.append(Recommendation(
                id='trend_accelerating_decline',
                category=Category.TREND,
                severity=Severity.MEDIUM,
                title='Beschleunigter Rückgang',
                message=f'Der Rückgang hat sich in den letzten 3 Monaten beschleunigt '
                       f'(aktuell {recent_trend_pct:.1f}% vs. Ø {trend_pct:.1f}%).',
                action='Kurzfristige Maßnahmen zur Stabilisierung prüfen',
                data_basis={'recent_trend': recent_trend_pct, 'overall_trend': trend_pct},
                confidence=0.7
            ))
        
        # Strong growth
        elif trend_pct > self.THRESHOLDS['strong_growth_pct']:
            self.recommendations.append(Recommendation(
                id='trend_strong_growth',
                category=Category.OPPORTUNITY,
                severity=Severity.INFO,
                title='Starkes Wachstum',
                message=f'Positiver Wachstumstrend von {trend_pct:.1f}% pro Monat erkannt. '
                       f'Potenzial: +€{slope*6:,.0f} in den nächsten 6 Monaten.'.replace(',', '.'),
                action='Kapazitäten und Ressourcen für weiteres Wachstum sicherstellen',
                data_basis={'trend_pct': trend_pct, 'projected_growth': slope * 6},
                confidence=min(0.85, len(monthly) / 12)
            ))
    
    # =========================================================================
    # Seasonality Analysis Rules
    # =========================================================================
    
    def _analyze_seasonality(self):
        """Analyze seasonal patterns."""
        if len(self.revenue_data) < 12:
            return
        
        df = self.revenue_data.copy()
        df['Month'] = df['Date'].dt.month
        df['Year'] = df['Date'].dt.year
        
        # Need at least some months with multiple years
        year_count = df['Year'].nunique()
        if year_count < 2:
            return
        
        monthly_avg = df.groupby('Month')['Amount'].mean()
        overall_avg = df['Amount'].sum() / df.groupby(['Year', 'Month']).ngroups
        
        # Seasonal indices
        seasonal_indices = (monthly_avg / overall_avg * 100) if overall_avg > 0 else monthly_avg * 0
        
        # Seasonality strength
        seasonality_strength = np.std(seasonal_indices)
        
        if seasonality_strength > self.THRESHOLDS['seasonal_strength']:
            month_names = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun',
                         'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
            
            strong_months = [(month_names[m-1], idx) for m, idx in seasonal_indices.items() if idx > 115]
            weak_months = [(month_names[m-1], idx) for m, idx in seasonal_indices.items() if idx < 85]
            
            # Get current month to check if we're approaching a weak period
            current_month = datetime.now().month
            upcoming_weak = [m for m, idx in seasonal_indices.items() 
                          if idx < 85 and m in [(current_month + i) % 12 + 1 for i in range(1, 4)]]
            
            if upcoming_weak:
                upcoming_names = [month_names[m-1] for m in upcoming_weak]
                self.recommendations.append(Recommendation(
                    id='seasonal_weak_upcoming',
                    category=Category.SEASONAL,
                    severity=Severity.MEDIUM,
                    title='Saisonales Tief voraus',
                    message=f'In den nächsten 3 Monaten ({", ".join(upcoming_names)}) sind historisch '
                           f'schwächere Einnahmen zu erwarten.',
                    action='Rücklagen bilden oder alternative Einnahmequellen für diese Periode planen',
                    data_basis={'weak_months': upcoming_names, 'seasonal_indices': dict(seasonal_indices)},
                    confidence=0.8
                ))
            
            if strong_months:
                self.recommendations.append(Recommendation(
                    id='seasonal_pattern_info',
                    category=Category.SEASONAL,
                    severity=Severity.INFO,
                    title='Saisonales Muster erkannt',
                    message=f'Starke Monate: {", ".join([m[0] for m in sorted(strong_months, key=lambda x: x[1], reverse=True)[:3]])}. '
                           f'Schwache Monate: {", ".join([m[0] for m in sorted(weak_months, key=lambda x: x[1])[:3]])}.',
                    action='Saisonale Planung in Budget und Ressourcen berücksichtigen',
                    data_basis={'strong': strong_months, 'weak': weak_months},
                    confidence=0.85
                ))
    
    # =========================================================================
    # Volatility Analysis Rules
    # =========================================================================
    
    def _analyze_volatility(self):
        """Analyze revenue volatility."""
        if len(self.revenue_data) < 6:
            return
        
        df = self.revenue_data.copy()
        df['YearMonth'] = df['Date'].dt.to_period('M')
        monthly = df.groupby('YearMonth')['Amount'].sum()
        
        # Coefficient of variation
        cv = monthly.std() / monthly.mean() if monthly.mean() > 0 else 0
        
        if cv > self.THRESHOLDS['high_volatility_cv']:
            self.recommendations.append(Recommendation(
                id='volatility_high',
                category=Category.RISK,
                severity=Severity.MEDIUM,
                title='Hohe Einnahmen-Volatilität',
                message=f'Die monatlichen Einnahmen schwanken stark (CV={cv:.1%}). '
                       f'Spanne: €{monthly.min():,.0f} - €{monthly.max():,.0f}.'.replace(',', '.'),
                action='Einnahmequellen diversifizieren oder stabilere Vertragsmodelle prüfen',
                data_basis={'cv': cv, 'min': monthly.min(), 'max': monthly.max(), 'mean': monthly.mean()},
                confidence=0.75
            ))
    
    # =========================================================================
    # Concentration Analysis Rules
    # =========================================================================
    
    def _analyze_concentration(self):
        """Analyze revenue concentration."""
        if len(self.revenue_data) < 3:
            return
        
        df = self.revenue_data.copy()
        
        # Check if single invoice is too large
        total = df['Amount'].sum()
        max_single = df['Amount'].max()
        
        if total > 0:
            concentration = max_single / total
            
            if concentration > self.THRESHOLDS['high_concentration']:
                self.recommendations.append(Recommendation(
                    id='concentration_single',
                    category=Category.RISK,
                    severity=Severity.HIGH,
                    title='Hohe Abhängigkeit von Einzelpositionen',
                    message=f'Eine einzelne Rechnung macht {concentration:.1%} der Gesamteinnahmen aus. '
                           f'Dies stellt ein Klumpenrisiko dar.',
                    action='Kundenbasis diversifizieren und Abhängigkeit reduzieren',
                    data_basis={'concentration': concentration, 'max_amount': max_single},
                    confidence=0.9
                ))
    
    # =========================================================================
    # Growth Analysis Rules
    # =========================================================================
    
    def _analyze_growth(self):
        """Analyze year-over-year growth."""
        if len(self.revenue_data) < 12:
            return
        
        df = self.revenue_data.copy()
        df['Year'] = df['Date'].dt.year
        
        yearly = df.groupby('Year')['Amount'].sum()
        
        if len(yearly) < 2:
            return
        
        years = sorted(yearly.index)
        current_year = years[-1]
        previous_year = years[-2]
        
        current = yearly[current_year]
        previous = yearly[previous_year]
        
        if previous > 0:
            yoy_growth = ((current - previous) / previous) * 100
            
            if yoy_growth < self.THRESHOLDS['yoy_decline_warning']:
                self.recommendations.append(Recommendation(
                    id='yoy_decline',
                    category=Category.TREND,
                    severity=Severity.HIGH,
                    title='Jahresvergleich negativ',
                    message=f'{current_year} liegt {abs(yoy_growth):.1f}% unter {previous_year}. '
                           f'Differenz: €{abs(current - previous):,.0f}.'.replace(',', '.'),
                    action='Ursachen für Rückgang analysieren und Maßnahmenplan erstellen',
                    data_basis={'yoy_growth': yoy_growth, 'current': current, 'previous': previous},
                    confidence=0.9
                ))
            
            elif yoy_growth > self.THRESHOLDS['yoy_growth_opportunity']:
                self.recommendations.append(Recommendation(
                    id='yoy_growth',
                    category=Category.OPPORTUNITY,
                    severity=Severity.INFO,
                    title='Starkes Jahreswachstum',
                    message=f'{current_year} liegt {yoy_growth:.1f}% über {previous_year}. '
                           f'Zuwachs: +€{current - previous:,.0f}.'.replace(',', '.'),
                    action='Wachstumstreiber identifizieren und weiter ausbauen',
                    data_basis={'yoy_growth': yoy_growth, 'current': current, 'previous': previous},
                    confidence=0.9
                ))
    
    # =========================================================================
    # Opportunity Analysis Rules
    # =========================================================================
    
    def _analyze_opportunities(self):
        """Identify opportunities for improvement."""
        if len(self.revenue_data) < 6:
            return
        
        df = self.revenue_data.copy()
        df['YearMonth'] = df['Date'].dt.to_period('M')
        monthly = df.groupby('YearMonth')['Amount'].sum()
        
        # Check for consecutive growth
        if len(monthly) >= 3:
            recent = monthly.tail(3).values
            if all(recent[i] < recent[i+1] for i in range(len(recent)-1)):
                growth_rate = ((recent[-1] - recent[0]) / recent[0]) * 100 if recent[0] > 0 else 0
                
                self.recommendations.append(Recommendation(
                    id='consecutive_growth',
                    category=Category.OPPORTUNITY,
                    severity=Severity.INFO,
                    title='3 Monate kontinuierliches Wachstum',
                    message=f'Die letzten 3 Monate zeigen kontinuierliches Wachstum (+{growth_rate:.1f}%). '
                           f'Dies deutet auf positive Marktentwicklung hin.',
                    action='Momentum nutzen und in Wachstum investieren',
                    data_basis={'recent_values': recent.tolist(), 'growth_rate': growth_rate},
                    confidence=0.7
                ))
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def get_recommendations_by_severity(self, severity: Severity) -> List[Recommendation]:
        """Filter recommendations by severity."""
        return [r for r in self.recommendations if r.severity == severity]
    
    def get_recommendations_by_category(self, category: Category) -> List[Recommendation]:
        """Filter recommendations by category."""
        return [r for r in self.recommendations if r.category == category]
    
    def get_high_priority_recommendations(self) -> List[Recommendation]:
        """Get high and critical severity recommendations."""
        return [r for r in self.recommendations 
                if r.severity in [Severity.HIGH, Severity.CRITICAL]]
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Convert all recommendations to list of dictionaries."""
        return [r.to_dict() for r in self.recommendations]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all recommendations."""
        return {
            'total': len(self.recommendations),
            'by_severity': {
                'critical': len(self.get_recommendations_by_severity(Severity.CRITICAL)),
                'high': len(self.get_recommendations_by_severity(Severity.HIGH)),
                'medium': len(self.get_recommendations_by_severity(Severity.MEDIUM)),
                'low': len(self.get_recommendations_by_severity(Severity.LOW)),
                'info': len(self.get_recommendations_by_severity(Severity.INFO)),
            },
            'by_category': {
                'trend': len(self.get_recommendations_by_category(Category.TREND)),
                'seasonal': len(self.get_recommendations_by_category(Category.SEASONAL)),
                'risk': len(self.get_recommendations_by_category(Category.RISK)),
                'opportunity': len(self.get_recommendations_by_category(Category.OPPORTUNITY)),
                'efficiency': len(self.get_recommendations_by_category(Category.EFFICIENCY)),
            }
        }

