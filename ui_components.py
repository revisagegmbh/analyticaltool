"""
UI Components Module - KPI Cards, Date Range Filter, Search, and Custom Widgets
Phase 3: Added Search/Filter Bar, Category Editor, Export Buttons
"""

from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any, Tuple
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QComboBox, QDateEdit, QPushButton, QGridLayout, QSizePolicy,
    QLineEdit, QSpinBox, QDoubleSpinBox, QMenu, QFileDialog, QMessageBox,
    QScrollArea, QCheckBox, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QAction

from styles import (
    COLORS, KPI_CARD_STYLE, KPI_VALUE_STYLE, KPI_LABEL_STYLE,
    KPI_TREND_POSITIVE, KPI_TREND_NEGATIVE, KPI_TREND_NEUTRAL
)
from data_manager import DataManager


class KPICard(QFrame):
    """A single KPI display card."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.init_ui()
    
    def init_ui(self):
        """Initialize the KPI card UI."""
        self.setStyleSheet(KPI_CARD_STYLE)
        self.setMinimumWidth(200)
        self.setMinimumHeight(120)  # Increased height to prevent text cutoff
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 16)  # Reduced top margin, kept bottom
        layout.setSpacing(6)
        
        # Title label
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet(KPI_LABEL_STYLE)
        layout.addWidget(self.title_label)
        
        # Value layout (value + trend)
        value_layout = QHBoxLayout()
        value_layout.setSpacing(12)
        
        # Value label
        self.value_label = QLabel("€0,00")
        self.value_label.setStyleSheet(KPI_VALUE_STYLE)
        value_layout.addWidget(self.value_label)
        
        # Trend label
        self.trend_label = QLabel("")
        self.trend_label.setStyleSheet(KPI_TREND_NEUTRAL)
        value_layout.addWidget(self.trend_label)
        
        value_layout.addStretch()
        layout.addLayout(value_layout)
        
        # Subtitle/detail label
        self.detail_label = QLabel("")
        self.detail_label.setStyleSheet(f"font-size: 11px; color: {COLORS['text_muted']}; background: transparent; border: none;")
        layout.addWidget(self.detail_label)
    
    def set_value(self, value: str, trend: Optional[str] = None, 
                  trend_direction: Optional[str] = None, detail: str = ""):
        """Update the KPI card values.
        
        Args:
            value: Main value to display.
            trend: Trend text (e.g., "+12.5%").
            trend_direction: 'positive', 'negative', or 'neutral'.
            detail: Additional detail text.
        """
        self.value_label.setText(value)
        
        if trend:
            if trend_direction == 'positive':
                self.trend_label.setStyleSheet(KPI_TREND_POSITIVE)
                self.trend_label.setText(f"↑ {trend}")
            elif trend_direction == 'negative':
                self.trend_label.setStyleSheet(KPI_TREND_NEGATIVE)
                self.trend_label.setText(f"↓ {trend}")
            else:
                self.trend_label.setStyleSheet(KPI_TREND_NEUTRAL)
                self.trend_label.setText(f"→ {trend}")
        else:
            self.trend_label.setText("")
        
        self.detail_label.setText(detail)


class KPIPanel(QWidget):
    """Panel containing all KPI cards."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the KPI panel."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Create KPI cards
        self.total_card = KPICard("GESAMTEINNAHMEN")
        self.avg_card = KPICard("Ø MONATLICH")
        self.high_card = KPICard("HÖCHSTER MONAT")
        self.yoy_card = KPICard("JAHRESVERGLEICH")
        
        layout.addWidget(self.total_card)
        layout.addWidget(self.avg_card)
        layout.addWidget(self.high_card)
        layout.addWidget(self.yoy_card)
    
    def update_kpis(self, kpis: Dict[str, Any]):
        """Update all KPI cards with new values.
        
        Args:
            kpis: Dictionary containing KPI values from DataManager.
        """
        # Total expenses
        total = kpis.get('total_expenses', 0)
        invoice_count = kpis.get('invoice_count', 0)
        self.total_card.set_value(
            f"€{total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            detail=f"{invoice_count} Rechnungen"
        )
        
        # Average monthly
        avg = kpis.get('avg_monthly', 0)
        mom = kpis.get('mom_change')
        if mom:
            trend_pct = mom['percentage']
            trend_text = f"{abs(trend_pct):.1f}%"
            trend_dir = 'positive' if trend_pct > 0 else ('negative' if trend_pct < 0 else 'neutral')
            self.avg_card.set_value(
                f"€{avg:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                trend=trend_text,
                trend_direction=trend_dir,
                detail=f"vs. {mom['previous_month']}"
            )
        else:
            self.avg_card.set_value(
                f"€{avg:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            )
        
        # Highest month
        high_month, high_amount = kpis.get('highest_month', ('N/A', 0))
        low_month, low_amount = kpis.get('lowest_month', ('N/A', 0))
        self.high_card.set_value(
            f"€{high_amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            detail=f"{high_month}"
        )
        
        # YoY Growth
        yoy = kpis.get('yoy_growth')
        if yoy is not None:
            trend_text = f"{abs(yoy):.1f}%"
            trend_dir = 'positive' if yoy > 0 else ('negative' if yoy < 0 else 'neutral')
            # Note: For expenses, growth might be considered negative from a cost perspective
            self.yoy_card.set_value(
                f"{yoy:+.1f}%",
                trend=trend_text,
                trend_direction=trend_dir,
                detail="vs. Vorjahr"
            )
        else:
            self.yoy_card.set_value(
                "—",
                detail="Nicht genug Daten"
            )


class DateRangeFilter(QWidget):
    """Date range filter widget with presets and period comparison."""
    
    # Signal emitted when date range changes (primary range)
    date_range_changed = pyqtSignal(object, object)  # start_date, end_date
    
    # Signal emitted when comparison mode changes
    comparison_changed = pyqtSignal(bool, object, object, object, object, str, str)  
    # (enabled, start1, end1, start2, end2, label1, label2)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.presets = DataManager.get_date_range_presets()
        self.comparison_enabled = False
        self.init_ui()
    
    def init_ui(self):
        """Initialize the date range filter UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Primary period label
        label = QLabel("Zeitraum:")
        label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 600;")
        layout.addWidget(label)
        
        # Primary preset dropdown
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(list(self.presets.keys()))
        self.preset_combo.setCurrentText("Gesamter Zeitraum")
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        self.preset_combo.setMinimumWidth(160)
        layout.addWidget(self.preset_combo)
        
        # Separator
        sep1 = QLabel("  |  ")
        sep1.setStyleSheet(f"color: {COLORS['border']};")
        layout.addWidget(sep1)
        
        # Comparison checkbox
        from PyQt6.QtWidgets import QCheckBox
        self.compare_checkbox = QCheckBox("Vergleich")
        self.compare_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS['text_secondary']};
                font-weight: 600;
                spacing: 6px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid {COLORS['border']};
                background-color: {COLORS['bg_elevated']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLORS['primary']};
                border-color: {COLORS['primary']};
            }}
            QCheckBox::indicator:hover {{
                border-color: {COLORS['primary_light']};
            }}
        """)
        self.compare_checkbox.stateChanged.connect(self.on_compare_toggled)
        layout.addWidget(self.compare_checkbox)
        
        # Comparison container (hidden by default)
        self.compare_container = QWidget()
        compare_layout = QHBoxLayout(self.compare_container)
        compare_layout.setContentsMargins(0, 0, 0, 0)
        compare_layout.setSpacing(8)
        
        vs_label = QLabel("vs.")
        vs_label.setStyleSheet(f"color: {COLORS['chart_orange']}; font-weight: 700;")
        compare_layout.addWidget(vs_label)
        
        # Secondary preset dropdown for comparison
        self.compare_combo = QComboBox()
        # Add comparison-friendly presets
        self.compare_combo.addItems(self._get_comparison_presets())
        self.compare_combo.setMinimumWidth(160)
        self.compare_combo.currentTextChanged.connect(self.on_comparison_preset_changed)
        compare_layout.addWidget(self.compare_combo)
        
        self.compare_container.setVisible(False)
        layout.addWidget(self.compare_container)
        
        layout.addStretch()
    
    def _get_comparison_presets(self) -> list:
        """Get presets suitable for comparison."""
        today = datetime.now()
        prev_year = today.year - 1
        prev_prev_year = today.year - 2
        
        return [
            f'Q1 {prev_year}',
            f'Q2 {prev_year}',
            f'Q3 {prev_year}',
            f'Q4 {prev_year}',
            f'Q1 {prev_prev_year}',
            f'Q2 {prev_prev_year}',
            f'Q3 {prev_prev_year}',
            f'Q4 {prev_prev_year}',
            f'Letztes Jahr',
            f'{prev_year}',
            f'{prev_prev_year}',
            'Vorjahr zum Zeitraum',
        ]
    
    def on_preset_changed(self, preset_name: str):
        """Handle primary preset selection change."""
        start_date, end_date = self.presets.get(preset_name, (None, None))
        if start_date and end_date:
            self.date_range_changed.emit(start_date, end_date)
            
            # If comparison is enabled, update it
            if self.comparison_enabled:
                self._emit_comparison()
    
    def on_compare_toggled(self, state):
        """Handle comparison checkbox toggle."""
        self.comparison_enabled = bool(state)
        self.compare_container.setVisible(self.comparison_enabled)
        
        if self.comparison_enabled:
            self._emit_comparison()
        else:
            # Emit comparison disabled
            self.comparison_changed.emit(False, None, None, None, None, '', '')
    
    def on_comparison_preset_changed(self, preset_name: str):
        """Handle comparison preset selection change."""
        if self.comparison_enabled:
            self._emit_comparison()
    
    def _emit_comparison(self):
        """Emit comparison data based on current selections."""
        # Get primary period
        primary_preset = self.preset_combo.currentText()
        primary_start, primary_end = self.presets.get(primary_preset, (None, None))
        
        if not primary_start or not primary_end:
            return
        
        # Get comparison period
        compare_preset = self.compare_combo.currentText()
        
        if compare_preset == 'Vorjahr zum Zeitraum':
            # Shift primary period back by one year
            compare_start = datetime(primary_start.year - 1, primary_start.month, primary_start.day)
            compare_end = datetime(primary_end.year - 1, primary_end.month, 
                                  min(primary_end.day, 28))  # Safe for all months
            compare_label = f"{primary_preset} (Vorjahr)"
        elif compare_preset in self.presets:
            compare_start, compare_end = self.presets.get(compare_preset, (None, None))
            compare_label = compare_preset
        else:
            # Try to parse year-based presets
            try:
                year = int(compare_preset)
                compare_start = datetime(year, 1, 1)
                compare_end = datetime(year, 12, 31)
                compare_label = str(year)
            except ValueError:
                # Try quarter format
                if compare_preset.startswith('Q') and ' ' in compare_preset:
                    parts = compare_preset.split(' ')
                    quarter = int(parts[0][1])
                    year = int(parts[1])
                    quarter_starts = {1: 1, 2: 4, 3: 7, 4: 10}
                    quarter_ends = {1: 3, 2: 6, 3: 9, 4: 12}
                    quarter_end_days = {1: 31, 2: 30, 3: 30, 4: 31}
                    compare_start = datetime(year, quarter_starts[quarter], 1)
                    compare_end = datetime(year, quarter_ends[quarter], quarter_end_days[quarter])
                    compare_label = compare_preset
                else:
                    return
        
        self.comparison_changed.emit(
            True,
            primary_start, primary_end,
            compare_start, compare_end,
            primary_preset, compare_label
        )
    
    def get_current_range(self) -> tuple:
        """Get the currently selected date range."""
        preset_name = self.preset_combo.currentText()
        return self.presets.get(preset_name, (None, None))
    
    def is_comparison_enabled(self) -> bool:
        """Check if comparison mode is enabled."""
        return self.comparison_enabled
    
    def get_comparison_data(self) -> dict:
        """Get current comparison configuration."""
        if not self.comparison_enabled:
            return None
        
        primary_preset = self.preset_combo.currentText()
        primary_start, primary_end = self.presets.get(primary_preset, (None, None))
        
        compare_preset = self.compare_combo.currentText()
        
        return {
            'primary_preset': primary_preset,
            'compare_preset': compare_preset,
            'primary_range': (primary_start, primary_end),
        }


class MonthlyComparisonTable(QWidget):
    """Table showing month-over-month comparison with trend indicators."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the comparison table."""
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel("Monatlicher Vergleich")
        title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 600;
            color: {COLORS['text_primary']};
            padding: 8px 0;
        """)
        layout.addWidget(title)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Monat', 'Betrag', 'Änderung', 'Trend'])
        
        # Configure header
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.table)
    
    def update_data(self, comparison_df):
        """Update the table with comparison data."""
        from PyQt6.QtWidgets import QTableWidgetItem
        
        if comparison_df.empty:
            self.table.setRowCount(0)
            return
        
        self.table.setRowCount(len(comparison_df))
        
        for i, row in comparison_df.iterrows():
            # Month
            month_item = QTableWidgetItem(str(row['YearMonth']))
            month_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 0, month_item)
            
            # Amount
            amount = row['Amount']
            amount_str = f"€{amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            amount_item = QTableWidgetItem(amount_str)
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 1, amount_item)
            
            # Change
            change = row.get('Change', 0)
            if pd.notna(change) and change != 0:
                change_str = f"€{change:+,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            else:
                change_str = "—"
            change_item = QTableWidgetItem(change_str)
            change_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 2, change_item)
            
            # Trend arrow
            change_pct = row.get('ChangePercent', 0)
            if pd.notna(change_pct) and change_pct != 0:
                if change_pct > 0:
                    trend_str = f"↑ {change_pct:.1f}%"
                    color = COLORS['kpi_positive']
                else:
                    trend_str = f"↓ {abs(change_pct):.1f}%"
                    color = COLORS['kpi_negative']
            else:
                trend_str = "→"
                color = COLORS['text_muted']
            
            trend_item = QTableWidgetItem(trend_str)
            trend_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            trend_item.setForeground(Qt.GlobalColor.white)  # Will be styled via stylesheet
            self.table.setItem(i, 3, trend_item)
        
        self.table.resizeColumnsToContents()


class ViewSelector(QWidget):
    """Widget for selecting different data views."""
    
    view_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the view selector."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        label = QLabel("Ansicht:")
        label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 600;")
        layout.addWidget(label)
        
        self.view_combo = QComboBox()
        self.view_combo.addItems([
            "Monatliche Summen",
            "Jährliche Summen", 
            "Alle Daten",
            "Monatsvergleich"
        ])
        self.view_combo.currentTextChanged.connect(self.view_changed.emit)
        self.view_combo.setMinimumWidth(160)
        layout.addWidget(self.view_combo)
        
        layout.addStretch()
    
    def current_view(self) -> str:
        """Get the currently selected view."""
        return self.view_combo.currentText()


# Import pandas for the comparison table
import pandas as pd


class SearchFilterBar(QWidget):
    """Amount filter bar for filtering invoices by amount range."""
    
    # Signal emitted when filter changes
    search_changed = pyqtSignal(str, str, float, float)  # query, category, min_amount, max_amount
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the filter bar."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Filter icon
        filter_label = QLabel("🔎 Filter:")
        filter_label.setStyleSheet(f"font-size: 14px; color: {COLORS['text_secondary']}; font-weight: 600;")
        layout.addWidget(filter_label)
        
        # Amount range filter
        amount_label = QLabel("Betrag:")
        amount_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 600;")
        layout.addWidget(amount_label)
        
        self.min_amount = QDoubleSpinBox()
        self.min_amount.setPrefix("€ ")
        self.min_amount.setRange(0, 9999999)
        self.min_amount.setDecimals(0)
        self.min_amount.setSpecialValueText("Min")
        self.min_amount.setValue(0)
        self.min_amount.setMinimumWidth(100)
        self.min_amount.valueChanged.connect(self.on_filter_changed)
        layout.addWidget(self.min_amount)
        
        to_label = QLabel("-")
        to_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(to_label)
        
        self.max_amount = QDoubleSpinBox()
        self.max_amount.setPrefix("€ ")
        self.max_amount.setRange(0, 9999999)
        self.max_amount.setDecimals(0)
        self.max_amount.setSpecialValueText("Max")
        self.max_amount.setValue(0)
        self.max_amount.setMinimumWidth(100)
        self.max_amount.valueChanged.connect(self.on_filter_changed)
        layout.addWidget(self.max_amount)
        
        # Clear filters button
        self.clear_btn = QPushButton("✕ Filter löschen")
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_muted']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                color: {COLORS['text_primary']};
                border-color: {COLORS['primary']};
            }}
        """)
        self.clear_btn.clicked.connect(self.clear_filters)
        layout.addWidget(self.clear_btn)
        
        layout.addStretch()
    
    def on_filter_changed(self):
        """Emit signal when filter changes."""
        min_amt = self.min_amount.value() if self.min_amount.value() > 0 else 0
        max_amt = self.max_amount.value() if self.max_amount.value() > 0 else 9999999
        
        # Emit with empty query and category for compatibility
        self.search_changed.emit('', 'Alle Kategorien', min_amt, max_amt)
    
    def clear_filters(self):
        """Clear all filters."""
        self.min_amount.setValue(0)
        self.max_amount.setValue(0)
        self.on_filter_changed()
    
    def get_filters(self) -> Dict:
        """Get current filter values."""
        return {
            'query': '',
            'category': 'Alle Kategorien',
            'min_amount': self.min_amount.value() if self.min_amount.value() > 0 else None,
            'max_amount': self.max_amount.value() if self.max_amount.value() > 0 else None
        }


class ExportPanel(QWidget):
    """Export buttons panel for CSV, Excel, and PDF export."""
    
    # Signals for export actions
    export_csv = pyqtSignal()
    export_excel = pyqtSignal()
    export_pdf = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the export panel."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Export label
        export_label = QLabel("Export:")
        export_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 600;")
        layout.addWidget(export_label)
        
        # CSV Button
        self.csv_btn = QPushButton("📄 CSV")
        self.csv_btn.setToolTip("Als CSV-Datei exportieren")
        self.csv_btn.setStyleSheet(self._get_export_btn_style())
        self.csv_btn.clicked.connect(self.export_csv.emit)
        layout.addWidget(self.csv_btn)
        
        # Excel Button
        self.excel_btn = QPushButton("📊 Excel")
        self.excel_btn.setToolTip("Als Excel-Datei exportieren")
        self.excel_btn.setStyleSheet(self._get_export_btn_style())
        self.excel_btn.clicked.connect(self.export_excel.emit)
        layout.addWidget(self.excel_btn)
        
        # PDF Button
        self.pdf_btn = QPushButton("📑 PDF")
        self.pdf_btn.setToolTip("Als PDF-Report exportieren")
        self.pdf_btn.setStyleSheet(self._get_export_btn_style())
        self.pdf_btn.clicked.connect(self.export_pdf.emit)
        layout.addWidget(self.pdf_btn)
    
    def _get_export_btn_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: {COLORS['bg_elevated']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_light']};
                border-color: {COLORS['primary']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['primary']};
            }}
        """


class CategoryEditorDialog(QWidget):
    """Inline category editor for table cells."""
    
    category_changed = pyqtSignal(str, str)  # expense_id, new_category
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_expense_id = None
    
    @staticmethod
    def create_category_combo() -> QComboBox:
        """Create a styled category combo box."""
        combo = QComboBox()
        combo.addItems(DataManager.CATEGORIES)
        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_elevated']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['primary']};
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 120px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['bg_medium']};
                color: {COLORS['text_primary']};
                selection-background-color: {COLORS['primary']};
            }}
        """)
        return combo


# =============================================================================
# Analytics Panel (Phase A: Analytics Engine - Extended Horizons)
# =============================================================================

class AnalyticsPanel(QWidget):
    """Panel displaying forecasts and recommendations with extended horizons."""
    
    forecast_requested = pyqtSignal(str)  # Forecast method name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.recommendations = []
        self.forecast_data = None
        self.extended_forecasts = {}
        self.init_ui()
    
    def init_ui(self):
        """Initialize the analytics panel with scrollable content."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        
        # Header (fixed, not scrolling)
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_medium']};
                border-bottom: 1px solid {COLORS['border']};
                padding: 4px;
            }}
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(8, 4, 8, 4)
        
        title = QLabel("📊 Analytics")
        title.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 700;
            color: {COLORS['text_primary']};
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Compact method selector
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "Jahrestrend",  # NEW: Best for quarterly data with high variance
            "Kombiniert",
            "Monte Carlo",
            "Ensemble",
            "Linear",
            "Exponentiell",
            "Gleitend",
            "Wachstum"
        ])
        self.method_combo.setMaximumWidth(120)
        self.method_combo.currentTextChanged.connect(self._on_method_changed)
        header_layout.addWidget(self.method_combo)
        
        main_layout.addWidget(header_frame)
        
        # Scrollable content area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: {COLORS['bg_dark']};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLORS['border']};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {COLORS['primary']};
            }}
        """)
        
        # Content widget inside scroll area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(10)
        
        # === PROGNOSE-HORIZONTE ===
        horizons_frame = QFrame()
        horizons_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
        """)
        horizons_layout = QVBoxLayout(horizons_frame)
        horizons_layout.setContentsMargins(10, 8, 10, 8)
        horizons_layout.setSpacing(6)
        
        # Horizons title
        horizons_title = QLabel("📅 Prognose-Horizonte")
        horizons_title.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 600;
            color: {COLORS['text_primary']};
            padding-bottom: 4px;
        """)
        horizons_layout.addWidget(horizons_title)
        
        # Grid for forecast horizons
        self.horizons_grid = QGridLayout()
        self.horizons_grid.setSpacing(4)
        
        # Create horizon labels (will be updated dynamically)
        self.horizon_labels = {}
        horizons = [
            ('next_month', 'Nächster Monat'),
            ('next_quarter', 'Nächstes Quartal'),
            ('next_year', 'Nächstes Jahr'),
            ('year_2', 'In 2 Jahren'),
            ('year_3', 'In 3 Jahren'),
        ]
        
        for i, (key, label) in enumerate(horizons):
            # Label
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
            self.horizons_grid.addWidget(lbl, i, 0)
            
            # Value
            val = QLabel("—")
            val.setStyleSheet(f"""
                color: {COLORS['text_primary']};
                font-size: 12px;
                font-weight: 600;
            """)
            val.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.horizons_grid.addWidget(val, i, 1)
            self.horizon_labels[key] = val
        
        horizons_layout.addLayout(self.horizons_grid)
        content_layout.addWidget(horizons_frame)
        
        # === TREND & KONFIDENZ ===
        trend_frame = QFrame()
        trend_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
        """)
        trend_layout = QVBoxLayout(trend_frame)
        trend_layout.setContentsMargins(10, 8, 10, 8)
        trend_layout.setSpacing(4)
        
        self.trend_label = QLabel("📈 Trend: —")
        self.trend_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 600;
            color: {COLORS['text_primary']};
        """)
        trend_layout.addWidget(self.trend_label)
        
        self.confidence_label = QLabel("Konfidenz: —")
        self.confidence_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        trend_layout.addWidget(self.confidence_label)
        
        self.method_info_label = QLabel("")
        self.method_info_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px;")
        self.method_info_label.setWordWrap(True)
        trend_layout.addWidget(self.method_info_label)
        
        content_layout.addWidget(trend_frame)
        
        # === EMPFEHLUNGEN ===
        rec_title = QLabel("💡 Empfehlungen")
        rec_title.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 600;
            color: {COLORS['text_primary']};
            padding-top: 4px;
        """)
        content_layout.addWidget(rec_title)
        
        # Recommendations container
        self.recommendations_container = QWidget()
        self.recommendations_layout = QVBoxLayout(self.recommendations_container)
        self.recommendations_layout.setContentsMargins(0, 0, 0, 0)
        self.recommendations_layout.setSpacing(6)
        content_layout.addWidget(self.recommendations_container)
        
        # Spacer at bottom
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
    
    def _on_method_changed(self, method: str):
        """Handle forecast method change."""
        method_map = {
            "Jahrestrend": "yearly_trend",  # NEW: Year-over-year trend analysis
            "Kombiniert": "combined",
            "Monte Carlo": "monte_carlo",
            "Ensemble": "ensemble",
            "Linear": "linear",
            "Exponentiell": "exponential",
            "Gleitend": "moving_average",
            "Wachstum": "growth_rate"
        }
        self.forecast_requested.emit(method_map.get(method, "combined"))
    
    def update_forecast(self, forecast_data: Dict[str, Any]):
        """Update the forecast display with extended horizons."""
        self.forecast_data = forecast_data
        
        if not forecast_data:
            self._clear_horizons()
            return
        
        # Get extended forecasts if available
        extended = forecast_data.get('extended_horizons', {})
        
        # Update horizon values
        horizons_map = {
            'next_month': extended.get('next_month'),
            'next_quarter': extended.get('next_quarter'),
            'next_year': extended.get('next_year'),
            'year_2': extended.get('year_2'),
            'year_3': extended.get('year_3'),
        }
        
        for key, value in horizons_map.items():
            if value is not None and key in self.horizon_labels:
                formatted = f"€{value:,.0f}".replace(',', '.')
                self.horizon_labels[key].setText(formatted)
                
                # Color based on trend (compare to current)
                if 'current_annual' in extended:
                    current = extended['current_annual']
                    if value > current * 1.05:
                        self.horizon_labels[key].setStyleSheet(f"""
                            color: {COLORS['kpi_positive']};
                            font-size: 12px;
                            font-weight: 600;
                        """)
                    elif value < current * 0.95:
                        self.horizon_labels[key].setStyleSheet(f"""
                            color: {COLORS['kpi_negative']};
                            font-size: 12px;
                            font-weight: 600;
                        """)
                    else:
                        self.horizon_labels[key].setStyleSheet(f"""
                            color: {COLORS['text_primary']};
                            font-size: 12px;
                            font-weight: 600;
                        """)
            else:
                if key in self.horizon_labels:
                    self.horizon_labels[key].setText("—")
        
        # Update trend and confidence
        interpretation = forecast_data.get('interpretation', {})
        trend = interpretation.get('trend', 'unbekannt')
        confidence = interpretation.get('confidence', 0)
        message = interpretation.get('message', '')
        method = forecast_data.get('method', 'Prognose')
        
        trend_icons = {
            'steigend': '📈',
            'fallend': '📉',
            'stabil': '➡️',
            'unbekannt': '❓'
        }
        trend_colors = {
            'steigend': COLORS['kpi_positive'],
            'fallend': COLORS['kpi_negative'],
            'stabil': COLORS['text_primary'],
            'unbekannt': COLORS['text_muted']
        }
        
        self.trend_label.setText(f"{trend_icons.get(trend, '❓')} Trend: {trend.capitalize()}")
        self.trend_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 600;
            color: {trend_colors.get(trend, COLORS['text_primary'])};
        """)
        
        # Check for probability (Monte Carlo / Ensemble)
        probability = interpretation.get('probability')
        if probability is not None and probability != confidence:
            prob_text = f"Wahrscheinlichkeit: {probability:.0%} | "
        else:
            prob_text = ""
        
        # Include data type info if available
        data_type_label = forecast_data.get('data_type_label', '')
        self.confidence_label.setText(f"{prob_text}Konfidenz: {confidence:.0%} | Methode: {method}")
        
        if data_type_label:
            self.method_info_label.setText(f"{message}\nDatentyp: {data_type_label}")
        else:
            self.method_info_label.setText(message)
    
    def _clear_horizons(self):
        """Clear all horizon values."""
        for label in self.horizon_labels.values():
            label.setText("—")
        self.trend_label.setText("📊 Trend: Keine Daten")
        self.confidence_label.setText("Konfidenz: —")
        self.method_info_label.setText("Laden Sie Daten um Prognosen zu generieren")
    
    def update_recommendations(self, recommendations: list):
        """Update the recommendations display."""
        self.recommendations = recommendations
        
        # Clear existing
        while self.recommendations_layout.count():
            child = self.recommendations_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not recommendations:
            no_rec = QLabel("✓ Keine dringenden Empfehlungen")
            no_rec.setStyleSheet(f"color: {COLORS['kpi_positive']}; padding: 6px; font-size: 11px;")
            self.recommendations_layout.addWidget(no_rec)
            return
        
        # Show top 4 recommendations (compact)
        for rec in recommendations[:4]:
            rec_widget = self._create_recommendation_widget(rec)
            self.recommendations_layout.addWidget(rec_widget)
    
    def _create_recommendation_widget(self, rec: Dict) -> QFrame:
        """Create a compact widget for a recommendation."""
        frame = QFrame()
        
        severity = rec.get('severity', 'info')
        severity_colors = {
            'critical': COLORS['chart_red'],
            'high': COLORS['chart_orange'],
            'medium': COLORS['chart_yellow'],
            'low': COLORS['chart_blue'],
            'info': COLORS['chart_cyan'],
        }
        border_color = severity_colors.get(severity, COLORS['border'])
        
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border-left: 3px solid {border_color};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)
        
        severity_icons = {
            'critical': '🚨',
            'high': '⚠️',
            'medium': '📋',
            'low': '💡',
            'info': 'ℹ️',
        }
        icon = severity_icons.get(severity, '•')
        
        # Title (compact)
        title = QLabel(f"{icon} {rec.get('title', 'Empfehlung')}")
        title.setStyleSheet(f"font-weight: 600; color: {COLORS['text_primary']}; font-size: 11px;")
        layout.addWidget(title)
        
        # Message (truncated)
        msg_text = rec.get('message', '')
        if len(msg_text) > 100:
            msg_text = msg_text[:97] + "..."
        msg = QLabel(msg_text)
        msg.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px;")
        msg.setWordWrap(True)
        layout.addWidget(msg)
        
        # Action (compact)
        action = QLabel(f"→ {rec.get('action', '')}")
        action.setStyleSheet(f"color: {COLORS['primary']}; font-size: 10px;")
        action.setWordWrap(True)
        layout.addWidget(action)
        
        return frame


class ForecastChartOverlay:
    """Helper class to add forecast overlay to charts."""
    
    @staticmethod
    def add_forecast_to_axes(ax, historical_x, historical_y, 
                             forecast_periods, forecast_values,
                             confidence_lower=None, confidence_upper=None,
                             color=None):
        """
        Add forecast visualization to matplotlib axes.
        
        Args:
            ax: Matplotlib axes
            historical_x: X values of historical data
            historical_y: Y values of historical data
            forecast_periods: Labels for forecast periods
            forecast_values: Forecast values
            confidence_lower: Lower confidence bound
            confidence_upper: Upper confidence bound
            color: Forecast line color
        """
        if not forecast_values:
            return
        
        if color is None:
            color = COLORS['chart_orange']
        
        # Calculate x positions for forecast
        start_x = len(historical_x)
        forecast_x = list(range(start_x, start_x + len(forecast_values)))
        
        # Connect last historical point to first forecast
        connect_x = [start_x - 1] + forecast_x
        connect_y = [historical_y[-1]] + forecast_values
        
        # Plot forecast line (dashed)
        ax.plot(
            connect_x, connect_y,
            color=color,
            linewidth=2.5,
            linestyle='--',
            marker='o',
            markersize=6,
            label='Prognose',
            alpha=0.9
        )
        
        # Add confidence interval
        if confidence_lower and confidence_upper:
            ax.fill_between(
                forecast_x,
                confidence_lower,
                confidence_upper,
                color=color,
                alpha=0.15,
                label='Konfidenzbereich'
            )
        
        # Add forecast value labels
        for i, (x, val) in enumerate(zip(forecast_x, forecast_values)):
            ax.annotate(
                f'€{val:,.0f}'.replace(',', '.'),
                xy=(x, val),
                xytext=(0, 10),
                textcoords='offset points',
                ha='center',
                va='bottom',
                fontsize=9,
                color=color,
                fontweight='bold',
                fontstyle='italic'
            )
        
        return forecast_x


# =============================================================================
# Marketing Campaign Dialog
# =============================================================================

class CampaignDialog(QWidget):
    """Dialog for adding/editing marketing campaigns."""
    
    campaign_saved = pyqtSignal(dict)  # Emitted when campaign is saved
    dialog_closed = pyqtSignal()
    
    # Platform options
    PLATFORMS = [
        "Google Ads",
        "Meta (Facebook/Instagram)",
        "LinkedIn Ads",
        "TikTok Ads",
        "Twitter/X Ads",
        "Pinterest Ads",
        "Microsoft Ads",
        "YouTube Ads",
        "Sonstige"
    ]
    
    def __init__(self, parent=None, campaign_data: Dict = None):
        """Initialize campaign dialog.
        
        Args:
            parent: Parent widget
            campaign_data: Existing campaign data for editing (None for new)
        """
        super().__init__(parent)
        self.campaign_data = campaign_data
        self.is_edit = campaign_data is not None
        self.init_ui()
        
        if self.is_edit:
            self.populate_fields()
    
    def init_ui(self):
        """Initialize the dialog UI."""
        self.setWindowTitle("Kampagne hinzufügen" if not self.is_edit else "Kampagne bearbeiten")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("📈 Marketing-Kampagne" if not self.is_edit else "📈 Kampagne bearbeiten")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {COLORS['text_primary']};
            padding-bottom: 8px;
        """)
        layout.addWidget(title)
        
        # Form container
        form_frame = QFrame()
        form_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        form_layout = QGridLayout(form_frame)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(16, 16, 16, 16)
        
        row = 0
        
        # Campaign Name
        form_layout.addWidget(self._create_label("Kampagnenname *"), row, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("z.B. Black Friday 2024")
        self._style_input(self.name_input)
        form_layout.addWidget(self.name_input, row, 1)
        row += 1
        
        # Platform
        form_layout.addWidget(self._create_label("Plattform *"), row, 0)
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(self.PLATFORMS)
        self._style_combo(self.platform_combo)
        form_layout.addWidget(self.platform_combo, row, 1)
        row += 1
        
        # Period Type
        form_layout.addWidget(self._create_label("Zeitraum-Typ"), row, 0)
        self.period_type_combo = QComboBox()
        self.period_type_combo.addItems(["Monat", "Quartal", "Jahr", "Benutzerdefiniert"])
        self.period_type_combo.currentTextChanged.connect(self._on_period_type_changed)
        self._style_combo(self.period_type_combo)
        form_layout.addWidget(self.period_type_combo, row, 1)
        row += 1
        
        # Period selector (for Month/Quarter/Year)
        form_layout.addWidget(self._create_label("Periode"), row, 0)
        self.period_container = QWidget()
        period_layout = QHBoxLayout(self.period_container)
        period_layout.setContentsMargins(0, 0, 0, 0)
        period_layout.setSpacing(8)
        
        # Month selector
        self.month_combo = QComboBox()
        self.month_combo.addItems([
            "Januar", "Februar", "März", "April", "Mai", "Juni",
            "Juli", "August", "September", "Oktober", "November", "Dezember"
        ])
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        self._style_combo(self.month_combo)
        period_layout.addWidget(self.month_combo)
        
        # Quarter selector
        self.quarter_combo = QComboBox()
        self.quarter_combo.addItems(["Q1", "Q2", "Q3", "Q4"])
        current_quarter = (datetime.now().month - 1) // 3
        self.quarter_combo.setCurrentIndex(current_quarter)
        self._style_combo(self.quarter_combo)
        self.quarter_combo.setVisible(False)
        period_layout.addWidget(self.quarter_combo)
        
        # Year selector
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2020, 2030)
        self.year_spin.setValue(datetime.now().year)
        self._style_spin(self.year_spin)
        period_layout.addWidget(self.year_spin)
        
        form_layout.addWidget(self.period_container, row, 1)
        row += 1
        
        # Custom date range (hidden by default)
        self.custom_date_container = QWidget()
        custom_date_layout = QHBoxLayout(self.custom_date_container)
        custom_date_layout.setContentsMargins(0, 0, 0, 0)
        custom_date_layout.setSpacing(8)
        
        custom_date_layout.addWidget(QLabel("Von:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        self._style_date_edit(self.start_date_edit)
        custom_date_layout.addWidget(self.start_date_edit)
        
        custom_date_layout.addWidget(QLabel("Bis:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self._style_date_edit(self.end_date_edit)
        custom_date_layout.addWidget(self.end_date_edit)
        
        self.custom_date_container.setVisible(False)
        form_layout.addWidget(self.custom_date_container, row, 0, 1, 2)
        row += 1
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {COLORS['border']};")
        form_layout.addWidget(separator, row, 0, 1, 2)
        row += 1
        
        # Budget
        form_layout.addWidget(self._create_label("Budget (€) *"), row, 0)
        self.budget_input = QDoubleSpinBox()
        self.budget_input.setRange(0, 10000000)
        self.budget_input.setDecimals(2)
        self.budget_input.setPrefix("€ ")
        self.budget_input.setSingleStep(100)
        self._style_spin(self.budget_input)
        form_layout.addWidget(self.budget_input, row, 1)
        row += 1
        
        # Impressions
        form_layout.addWidget(self._create_label("Impressionen"), row, 0)
        self.impressions_input = QSpinBox()
        self.impressions_input.setRange(0, 1000000000)
        self.impressions_input.setSingleStep(1000)
        self._style_spin(self.impressions_input)
        form_layout.addWidget(self.impressions_input, row, 1)
        row += 1
        
        # Clicks
        form_layout.addWidget(self._create_label("Klicks"), row, 0)
        self.clicks_input = QSpinBox()
        self.clicks_input.setRange(0, 100000000)
        self.clicks_input.setSingleStep(100)
        self._style_spin(self.clicks_input)
        form_layout.addWidget(self.clicks_input, row, 1)
        row += 1
        
        # Conversions
        form_layout.addWidget(self._create_label("Conversions"), row, 0)
        self.conversions_input = QSpinBox()
        self.conversions_input.setRange(0, 10000000)
        self.conversions_input.setSingleStep(10)
        self._style_spin(self.conversions_input)
        form_layout.addWidget(self.conversions_input, row, 1)
        row += 1
        
        # Revenue
        form_layout.addWidget(self._create_label("Umsatz (€)"), row, 0)
        self.revenue_input = QDoubleSpinBox()
        self.revenue_input.setRange(0, 100000000)
        self.revenue_input.setDecimals(2)
        self.revenue_input.setPrefix("€ ")
        self.revenue_input.setSingleStep(100)
        self._style_spin(self.revenue_input)
        form_layout.addWidget(self.revenue_input, row, 1)
        row += 1
        
        # Notes
        form_layout.addWidget(self._create_label("Notizen"), row, 0)
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Optionale Notizen zur Kampagne...")
        self._style_input(self.notes_input)
        form_layout.addWidget(self.notes_input, row, 1)
        row += 1
        
        layout.addWidget(form_frame)
        
        # Live KPI Preview
        kpi_frame = QFrame()
        kpi_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_medium']};
                border: 1px solid {COLORS['primary']};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        kpi_layout = QHBoxLayout(kpi_frame)
        kpi_layout.setSpacing(16)
        
        kpi_title = QLabel("📊 Vorschau KPIs:")
        kpi_title.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 600;")
        kpi_layout.addWidget(kpi_title)
        
        self.roas_preview = QLabel("ROAS: —")
        self.roas_preview.setStyleSheet(f"color: {COLORS['chart_green']}; font-weight: 600;")
        kpi_layout.addWidget(self.roas_preview)
        
        self.ctr_preview = QLabel("CTR: —")
        self.ctr_preview.setStyleSheet(f"color: {COLORS['chart_blue']}; font-weight: 600;")
        kpi_layout.addWidget(self.ctr_preview)
        
        self.cpc_preview = QLabel("CPC: —")
        self.cpc_preview.setStyleSheet(f"color: {COLORS['chart_orange']}; font-weight: 600;")
        kpi_layout.addWidget(self.cpc_preview)
        
        kpi_layout.addStretch()
        layout.addWidget(kpi_frame)
        
        # Connect inputs to update preview
        self.budget_input.valueChanged.connect(self._update_kpi_preview)
        self.impressions_input.valueChanged.connect(self._update_kpi_preview)
        self.clicks_input.valueChanged.connect(self._update_kpi_preview)
        self.revenue_input.valueChanged.connect(self._update_kpi_preview)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 Speichern" if not self.is_edit else "💾 Aktualisieren")
        save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def _create_label(self, text: str) -> QLabel:
        """Create a styled form label."""
        label = QLabel(text)
        label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 12px;
            font-weight: 500;
        """)
        return label
    
    def _style_input(self, widget: QLineEdit):
        """Apply styling to input fields."""
        widget.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_elevated']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['primary']};
            }}
        """)
    
    def _style_combo(self, widget: QComboBox):
        """Apply styling to combo boxes."""
        widget.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_elevated']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 6px 10px;
                min-width: 150px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['bg_medium']};
                color: {COLORS['text_primary']};
                selection-background-color: {COLORS['primary']};
            }}
        """)
    
    def _style_spin(self, widget):
        """Apply styling to spin boxes."""
        widget.setStyleSheet(f"""
            QSpinBox, QDoubleSpinBox {{
                background-color: {COLORS['bg_elevated']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 6px 10px;
                min-width: 150px;
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border-color: {COLORS['primary']};
            }}
        """)
    
    def _style_date_edit(self, widget: QDateEdit):
        """Apply styling to date edits."""
        widget.setStyleSheet(f"""
            QDateEdit {{
                background-color: {COLORS['bg_elevated']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 6px 10px;
            }}
            QDateEdit:focus {{
                border-color: {COLORS['primary']};
            }}
        """)
    
    def _on_period_type_changed(self, period_type: str):
        """Handle period type change."""
        self.month_combo.setVisible(period_type == "Monat")
        self.quarter_combo.setVisible(period_type == "Quartal")
        self.year_spin.setVisible(period_type in ["Monat", "Quartal", "Jahr"])
        self.custom_date_container.setVisible(period_type == "Benutzerdefiniert")
    
    def _update_kpi_preview(self):
        """Update KPI preview based on current inputs."""
        budget = self.budget_input.value()
        impressions = self.impressions_input.value()
        clicks = self.clicks_input.value()
        revenue = self.revenue_input.value()
        
        # ROAS
        if budget > 0:
            roas = revenue / budget
            color = COLORS['chart_green'] if roas >= 2 else (
                COLORS['chart_yellow'] if roas >= 1 else COLORS['chart_red']
            )
            self.roas_preview.setText(f"ROAS: {roas:.2f}")
            self.roas_preview.setStyleSheet(f"color: {color}; font-weight: 600;")
        else:
            self.roas_preview.setText("ROAS: —")
        
        # CTR
        if impressions > 0:
            ctr = clicks / impressions * 100
            self.ctr_preview.setText(f"CTR: {ctr:.2f}%")
        else:
            self.ctr_preview.setText("CTR: —")
        
        # CPC
        if clicks > 0:
            cpc = budget / clicks
            self.cpc_preview.setText(f"CPC: €{cpc:.2f}")
        else:
            self.cpc_preview.setText("CPC: —")
    
    def _get_date_range(self) -> Tuple[datetime, datetime]:
        """Get the date range based on period type selection."""
        period_type = self.period_type_combo.currentText()
        year = self.year_spin.value()
        
        if period_type == "Monat":
            month = self.month_combo.currentIndex() + 1
            start = datetime(year, month, 1)
            # End of month
            if month == 12:
                end = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end = datetime(year, month + 1, 1) - timedelta(days=1)
            return start, end.replace(hour=23, minute=59, second=59)
        
        elif period_type == "Quartal":
            quarter = self.quarter_combo.currentIndex()
            start_month = quarter * 3 + 1
            start = datetime(year, start_month, 1)
            end_month = start_month + 2
            if end_month == 12:
                end = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end = datetime(year, end_month + 1, 1) - timedelta(days=1)
            return start, end.replace(hour=23, minute=59, second=59)
        
        elif period_type == "Jahr":
            start = datetime(year, 1, 1)
            end = datetime(year, 12, 31, 23, 59, 59)
            return start, end
        
        else:  # Benutzerdefiniert
            start = self.start_date_edit.date().toPyDate()
            end = self.end_date_edit.date().toPyDate()
            return datetime.combine(start, datetime.min.time()), \
                   datetime.combine(end, datetime.max.time())
    
    def populate_fields(self):
        """Populate fields with existing campaign data."""
        if not self.campaign_data:
            return
        
        self.name_input.setText(self.campaign_data.get('Campaign_Name', ''))
        
        platform = self.campaign_data.get('Platform', '')
        idx = self.platform_combo.findText(platform)
        if idx >= 0:
            self.platform_combo.setCurrentIndex(idx)
        
        self.budget_input.setValue(float(self.campaign_data.get('Budget', 0)))
        self.impressions_input.setValue(int(self.campaign_data.get('Impressions', 0)))
        self.clicks_input.setValue(int(self.campaign_data.get('Clicks', 0)))
        self.conversions_input.setValue(int(self.campaign_data.get('Conversions', 0)))
        self.revenue_input.setValue(float(self.campaign_data.get('Revenue', 0)))
        self.notes_input.setText(self.campaign_data.get('Notes', ''))
        
        # Set to custom dates if editing
        self.period_type_combo.setCurrentText("Benutzerdefiniert")
        start_date = self.campaign_data.get('Start_Date')
        end_date = self.campaign_data.get('End_Date')
        if start_date:
            self.start_date_edit.setDate(QDate(start_date.year, start_date.month, start_date.day))
        if end_date:
            self.end_date_edit.setDate(QDate(end_date.year, end_date.month, end_date.day))
        
        self._update_kpi_preview()
    
    def _on_save(self):
        """Save the campaign."""
        # Validate
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie einen Kampagnennamen ein.")
            return
        
        budget = self.budget_input.value()
        if budget <= 0:
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie ein Budget > 0 ein.")
            return
        
        start_date, end_date = self._get_date_range()
        
        campaign_data = {
            'name': name,
            'platform': self.platform_combo.currentText(),
            'period_type': self.period_type_combo.currentText(),
            'start_date': start_date,
            'end_date': end_date,
            'budget': budget,
            'impressions': self.impressions_input.value(),
            'clicks': self.clicks_input.value(),
            'conversions': self.conversions_input.value(),
            'revenue': self.revenue_input.value(),
            'notes': self.notes_input.text()
        }
        
        # Include ID if editing
        if self.is_edit and self.campaign_data:
            campaign_data['id'] = self.campaign_data.get('ID')
        
        self.campaign_saved.emit(campaign_data)
    
    def _on_cancel(self):
        """Cancel and close dialog."""
        self.dialog_closed.emit()


# =============================================================================
# Manual Entry Dialog
# =============================================================================

class ManualEntryDialog(QDialog):
    """Dialog for manual data entry with period selection (Month/Quarter/Year).
    
    Supports both creating new entries and editing existing ones.
    """
    
    entry_saved = pyqtSignal(dict)  # Emitted when entry is saved (new or updated)
    entry_deleted = pyqtSignal(str)  # Emitted when entry is deleted (expense_id)
    
    MONTHS = [
        "Januar", "Februar", "März", "April", "Mai", "Juni",
        "Juli", "August", "September", "Oktober", "November", "Dezember"
    ]
    
    QUARTERS = ["Q1 (Jan-Mär)", "Q2 (Apr-Jun)", "Q3 (Jul-Sep)", "Q4 (Okt-Dez)"]
    
    def __init__(self, parent=None, dashboard_type: str = "revenue", 
                 existing_data: Dict = None):
        """Initialize manual entry dialog.
        
        Args:
            parent: Parent widget
            dashboard_type: 'revenue' or 'expenses'
            existing_data: Existing entry data for editing (None for new entry)
        """
        super().__init__(parent)
        self.dashboard_type = dashboard_type
        self.existing_data = existing_data
        self.is_edit = existing_data is not None
        self.expense_id = existing_data.get('ID') if existing_data else None
        self.init_ui()
        
        # Populate fields if editing
        if self.is_edit:
            self._populate_from_existing()
    
    def init_ui(self):
        """Initialize the dialog UI."""
        title_prefix = "Einnahme" if self.dashboard_type == "revenue" else "Ausgabe"
        action = "bearbeiten" if self.is_edit else "manuell eingeben"
        self.setWindowTitle(f"{title_prefix} {action}")
        self.setMinimumWidth(400)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        icon = "✏️" if self.is_edit else ("💰" if self.dashboard_type == "revenue" else "💸")
        title_text = f"{title_prefix} bearbeiten" if self.is_edit else f"{title_prefix} manuell erfassen"
        title = QLabel(f"{icon} {title_text}")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {COLORS['text_primary']};
            padding-bottom: 8px;
        """)
        layout.addWidget(title)
        
        # Form container
        form_frame = QFrame()
        form_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        form_layout = QGridLayout(form_frame)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(16, 16, 16, 16)
        
        row = 0
        
        # Period Type Selection
        form_layout.addWidget(self._create_label("Zeitraum-Typ *"), row, 0)
        self.period_type_combo = QComboBox()
        self.period_type_combo.addItems(["Monat", "Quartal", "Jahr"])
        self._style_combo(self.period_type_combo)
        self.period_type_combo.currentTextChanged.connect(self._on_period_type_changed)
        form_layout.addWidget(self.period_type_combo, row, 1)
        row += 1
        
        # Year Selection
        form_layout.addWidget(self._create_label("Jahr *"), row, 0)
        self.year_spinbox = QSpinBox()
        self.year_spinbox.setRange(2015, 2035)
        self.year_spinbox.setValue(datetime.now().year)
        self._style_spinbox(self.year_spinbox)
        form_layout.addWidget(self.year_spinbox, row, 1)
        row += 1
        
        # Month Selection (visible for "Monat")
        self.month_label = self._create_label("Monat *")
        form_layout.addWidget(self.month_label, row, 0)
        self.month_combo = QComboBox()
        self.month_combo.addItems(self.MONTHS)
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        self._style_combo(self.month_combo)
        form_layout.addWidget(self.month_combo, row, 1)
        row += 1
        
        # Quarter Selection (hidden by default)
        self.quarter_label = self._create_label("Quartal *")
        form_layout.addWidget(self.quarter_label, row, 0)
        self.quarter_combo = QComboBox()
        self.quarter_combo.addItems(self.QUARTERS)
        current_quarter = (datetime.now().month - 1) // 3
        self.quarter_combo.setCurrentIndex(current_quarter)
        self._style_combo(self.quarter_combo)
        form_layout.addWidget(self.quarter_combo, row, 1)
        self.quarter_label.setVisible(False)
        self.quarter_combo.setVisible(False)
        row += 1
        
        # Amount Input
        amount_label_text = "Betrag (EUR) *"
        form_layout.addWidget(self._create_label(amount_label_text), row, 0)
        self.amount_spinbox = QDoubleSpinBox()
        self.amount_spinbox.setRange(0.01, 99999999.99)
        self.amount_spinbox.setDecimals(2)
        self.amount_spinbox.setSuffix(" €")
        self.amount_spinbox.setValue(0.00)
        self._style_double_spinbox(self.amount_spinbox)
        form_layout.addWidget(self.amount_spinbox, row, 1)
        row += 1
        
        # Description (optional)
        form_layout.addWidget(self._create_label("Beschreibung"), row, 0)
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("z.B. Umsatz März 2021")
        self._style_input(self.description_input)
        form_layout.addWidget(self.description_input, row, 1)
        row += 1
        
        layout.addWidget(form_frame)
        
        # Info text
        info_label = QLabel("* Pflichtfelder")
        info_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        layout.addWidget(info_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Delete button (only in edit mode)
        if self.is_edit:
            self.delete_btn = QPushButton("Löschen")
            self.delete_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['kpi_negative']};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 24px;
                    font-weight: 600;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: #ff4444;
                }}
            """)
            self.delete_btn.clicked.connect(self._on_delete)
            button_layout.addWidget(self.delete_btn)
        
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Abbrechen")
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_elevated']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_light']};
            }}
        """)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        save_text = "Aktualisieren" if self.is_edit else "Speichern"
        self.save_btn = QPushButton(save_text)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_light']};
            }}
        """)
        self.save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
        
        # Apply dialog styling
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_medium']};
            }}
        """)
    
    def _create_label(self, text: str) -> QLabel:
        """Create a styled form label."""
        label = QLabel(text)
        label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-weight: 600;
            font-size: 13px;
        """)
        return label
    
    def _style_combo(self, combo: QComboBox):
        """Apply styling to combo box."""
        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_elevated']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                min-width: 200px;
            }}
            QComboBox:hover {{
                border-color: {COLORS['primary']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {COLORS['text_secondary']};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['bg_medium']};
                color: {COLORS['text_primary']};
                selection-background-color: {COLORS['primary']};
                border: 1px solid {COLORS['border']};
            }}
        """)
    
    def _style_spinbox(self, spinbox: QSpinBox):
        """Apply styling to spin box."""
        spinbox.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS['bg_elevated']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                min-width: 200px;
            }}
            QSpinBox:hover {{
                border-color: {COLORS['primary']};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 20px;
                border: none;
                background-color: {COLORS['bg_light']};
            }}
        """)
    
    def _style_double_spinbox(self, spinbox: QDoubleSpinBox):
        """Apply styling to double spin box."""
        spinbox.setStyleSheet(f"""
            QDoubleSpinBox {{
                background-color: {COLORS['bg_elevated']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                min-width: 200px;
            }}
            QDoubleSpinBox:hover {{
                border-color: {COLORS['primary']};
            }}
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
                width: 20px;
                border: none;
                background-color: {COLORS['bg_light']};
            }}
        """)
    
    def _style_input(self, input_widget: QLineEdit):
        """Apply styling to line edit."""
        input_widget.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_elevated']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                min-width: 200px;
            }}
            QLineEdit:hover {{
                border-color: {COLORS['primary']};
            }}
            QLineEdit:focus {{
                border-color: {COLORS['primary']};
            }}
            QLineEdit::placeholder {{
                color: {COLORS['text_muted']};
            }}
        """)
    
    def _on_period_type_changed(self, period_type: str):
        """Handle period type selection change."""
        is_month = period_type == "Monat"
        is_quarter = period_type == "Quartal"
        
        self.month_label.setVisible(is_month)
        self.month_combo.setVisible(is_month)
        self.quarter_label.setVisible(is_quarter)
        self.quarter_combo.setVisible(is_quarter)
        
        # Adjust dialog size
        self.adjustSize()
    
    def _populate_from_existing(self):
        """Populate form fields from existing data."""
        if not self.existing_data:
            return
        
        # Set amount
        amount = self.existing_data.get('Amount', 0)
        self.amount_spinbox.setValue(float(amount))
        
        # Set description
        description = self.existing_data.get('Description', '')
        self.description_input.setText(description)
        
        # Set PeriodType if available
        period_type = self.existing_data.get('PeriodType', 'monthly')
        period_type_map = {
            'monthly': 'Monat',
            'quarterly': 'Quartal',
            'yearly': 'Jahr'
        }
        period_type_display = period_type_map.get(period_type, 'Monat')
        index = self.period_type_combo.findText(period_type_display)
        if index >= 0:
            self.period_type_combo.setCurrentIndex(index)
            self._on_period_type_changed(period_type_display)
        
        # Parse date to set year and month/quarter
        date_val = self.existing_data.get('Date')
        if date_val is not None:
            # Convert to datetime if needed
            if hasattr(date_val, 'year'):
                year = date_val.year
                month = date_val.month
            else:
                # Try parsing string
                try:
                    from datetime import datetime as dt
                    if isinstance(date_val, str):
                        date_val = dt.strptime(date_val[:10], '%Y-%m-%d')
                    year = date_val.year
                    month = date_val.month
                except:
                    year = datetime.now().year
                    month = datetime.now().month
            
            self.year_spinbox.setValue(year)
            self.month_combo.setCurrentIndex(month - 1)
            
            # Determine quarter
            quarter = (month - 1) // 3
            self.quarter_combo.setCurrentIndex(quarter)
    
    def _on_delete(self):
        """Handle delete button click."""
        reply = QMessageBox.question(
            self,
            "Eintrag löschen",
            "Möchten Sie diesen Eintrag wirklich löschen?\n\n"
            "Diese Aktion kann nicht rückgängig gemacht werden.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.entry_deleted.emit(self.expense_id)
            self.accept()
    
    def _on_save(self):
        """Validate and save the entry."""
        amount = self.amount_spinbox.value()
        
        if amount <= 0:
            QMessageBox.warning(
                self,
                "Eingabefehler",
                "Bitte geben Sie einen Betrag größer als 0 ein."
            )
            return
        
        # Calculate date based on period type
        year = self.year_spinbox.value()
        period_type = self.period_type_combo.currentText()
        
        if period_type == "Monat":
            month = self.month_combo.currentIndex() + 1
            # Middle of month
            entry_date = datetime(year, month, 15)
            description_default = f"{self.MONTHS[month-1]} {year}"
        elif period_type == "Quartal":
            quarter = self.quarter_combo.currentIndex() + 1
            # Middle of quarter (month 2, 5, 8, 11)
            middle_month = (quarter - 1) * 3 + 2
            entry_date = datetime(year, middle_month, 15)
            description_default = f"Q{quarter} {year}"
        else:  # Jahr
            # Middle of year
            entry_date = datetime(year, 7, 1)
            description_default = f"Jahr {year}"
        
        # Use custom description or default
        description = self.description_input.text().strip()
        if not description:
            description = description_default
        
        # Map period type to standard format
        period_type_map = {
            'Monat': 'monthly',
            'Quartal': 'quarterly',
            'Jahr': 'yearly'
        }
        
        # Create entry data
        entry_data = {
            'Date': entry_date,
            'Amount': amount,
            'Description': description,
            'Source': 'Manuelle Eingabe',
            'Category': 'Manuell',
            'Vendor': '',
            'Currency': 'EUR',
            'PeriodType': period_type_map.get(period_type, 'monthly')  # NEW: Store period type
        }
        
        # Include ID if editing
        if self.is_edit and self.expense_id:
            entry_data['ID'] = self.expense_id
            entry_data['_is_update'] = True
        
        self.entry_saved.emit(entry_data)
        self.accept()

