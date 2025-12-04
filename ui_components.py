"""
UI Components Module - KPI Cards, Date Range Filter, Search, and Custom Widgets
Phase 3: Added Search/Filter Bar, Category Editor, Export Buttons
"""

from datetime import datetime
from typing import Optional, Callable, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QComboBox, QDateEdit, QPushButton, QGridLayout, QSizePolicy,
    QLineEdit, QSpinBox, QDoubleSpinBox, QMenu, QFileDialog, QMessageBox
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

