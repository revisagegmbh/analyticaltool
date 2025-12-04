"""
PDF Expense Tracker - Business Intelligence Dashboard
Main Application Entry Point

Phase 1 Features:
- PDF invoice parsing (German format)
- KPI dashboard with trend analysis
- Multi-select date range filter
- Month-over-month comparison
- Trend line visualization
- JSON data persistence

Phase 2 Features:
- Multiple chart types (Bar, Line, Pie, Donut, Heatmap, Stacked)
- Drill-down capability (Year → Month → Invoice)
- Interactive tooltips
- Period comparison

Phase 3 Features:
- Category tagging for invoices
- Search and filter functionality
- Export to CSV, Excel, PDF

Designed for Desktop App distribution (PyInstaller compatible)
"""

import sys
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import pdfplumber
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QFileDialog, 
    QLabel, QMessageBox, QSplitter, QFrame, QHeaderView, QComboBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont

# Local modules
from styles import MAIN_STYLESHEET, COLORS, apply_matplotlib_style
from data_manager import DataManager
from ui_components import (
    KPIPanel, DateRangeFilter, ViewSelector, 
    SearchFilterBar, ExportPanel, CategoryEditorDialog,
    AnalyticsPanel
)
from charts import ExpenseChart

# Analytics Engine (Phase A)
from analytics import ForecastEngine, RecommendationEngine


class ExpenseTrackerApp(QMainWindow):
    """Main application window with Business Intelligence Dashboard."""
    
    APP_NAME = "Rechnungsanalyse-Tool"
    APP_VERSION = "3.1.0"  # Phase A: Analytics Engine
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{self.APP_NAME} v{self.APP_VERSION}")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 700)
        
        # Apply dark theme
        self.setStyleSheet(MAIN_STYLESHEET)
        apply_matplotlib_style()
        
        # Initialize data manager
        self.data_manager = DataManager()
        
        # Current filter state
        self.current_start_date = None
        self.current_end_date = None
        
        # Comparison state
        self.comparison_enabled = False
        self.comparison_data = None  # Dict with comparison ranges and labels
        
        # Drill-down state
        self.drill_year = None
        self.drill_month = None
        
        # Setup UI
        self.init_ui()
        
        # Connect drill-down signals
        self.chart.drill_down_requested.connect(self.handle_drill_down)
        
        # Load initial data
        self.refresh_all()
    
    def init_ui(self):
        """Initialize the main UI layout."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        
        # ===== Header Section =====
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel(self.APP_NAME)
        title_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 700;
            color: {COLORS['text_primary']};
            letter-spacing: -1px;
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Action buttons
        self.load_btn = QPushButton("📁 PDF Laden")
        self.load_btn.setMinimumWidth(140)
        self.load_btn.clicked.connect(self.load_pdfs)
        header_layout.addWidget(self.load_btn)
        
        self.clear_btn = QPushButton("🗑️ Daten löschen")
        self.clear_btn.setProperty("class", "secondary")
        self.clear_btn.setMinimumWidth(140)
        self.clear_btn.clicked.connect(self.clear_data)
        header_layout.addWidget(self.clear_btn)
        
        main_layout.addLayout(header_layout)
        
        # ===== KPI Cards Section =====
        self.kpi_panel = KPIPanel()
        main_layout.addWidget(self.kpi_panel)
        
        # ===== Filter Section =====
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(12, 8, 12, 8)
        
        # Date range filter with comparison support
        self.date_filter = DateRangeFilter()
        self.date_filter.date_range_changed.connect(self.on_date_range_changed)
        self.date_filter.comparison_changed.connect(self.on_comparison_changed)
        filter_layout.addWidget(self.date_filter)
        
        # View selector
        self.view_selector = ViewSelector()
        self.view_selector.view_changed.connect(self.on_view_changed)
        filter_layout.addWidget(self.view_selector)
        
        # Export panel (Phase 3)
        self.export_panel = ExportPanel()
        self.export_panel.export_csv.connect(self.export_to_csv)
        self.export_panel.export_excel.connect(self.export_to_excel)
        self.export_panel.export_pdf.connect(self.export_to_pdf)
        filter_layout.addWidget(self.export_panel)
        
        main_layout.addWidget(filter_frame)
        
        # ===== Search/Filter Bar (Phase 3) =====
        search_frame = QFrame()
        search_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_medium']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 4px;
            }}
        """)
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(12, 8, 12, 8)
        
        self.search_filter = SearchFilterBar()
        self.search_filter.search_changed.connect(self.on_search_changed)
        search_layout.addWidget(self.search_filter)
        
        main_layout.addWidget(search_frame)
        
        # ===== Main Content (Splitter) =====
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {COLORS['border']};
                height: 3px;
            }}
            QSplitter::handle:hover {{
                background-color: {COLORS['primary']};
            }}
        """)
        
        # Top row: Chart + Analytics Panel (horizontal splitter)
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {COLORS['border']};
                width: 3px;
            }}
            QSplitter::handle:hover {{
                background-color: {COLORS['primary']};
            }}
        """)
        
        # Chart section
        chart_container = QFrame()
        chart_container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_medium']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(16, 16, 16, 16)
        
        self.chart = ExpenseChart()
        chart_layout.addWidget(self.chart)
        
        top_splitter.addWidget(chart_container)
        
        # Analytics Panel (Phase A)
        analytics_container = QFrame()
        analytics_container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_medium']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        analytics_layout = QVBoxLayout(analytics_container)
        analytics_layout.setContentsMargins(16, 16, 16, 16)
        
        self.analytics_panel = AnalyticsPanel()
        self.analytics_panel.forecast_requested.connect(self.on_forecast_method_changed)
        analytics_layout.addWidget(self.analytics_panel)
        
        top_splitter.addWidget(analytics_container)
        
        # Set horizontal splitter sizes (75% chart, 25% analytics)
        top_splitter.setSizes([800, 280])
        
        splitter.addWidget(top_splitter)
        
        # Table section
        table_container = QFrame()
        table_container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_medium']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(16, 16, 16, 16)
        
        # Table header
        table_header = QHBoxLayout()
        table_title = QLabel("Datenübersicht")
        table_title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 600;
            color: {COLORS['text_primary']};
        """)
        table_header.addWidget(table_title)
        
        # Status label
        self.status_label = QLabel("Keine Daten geladen")
        self.status_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        table_header.addStretch()
        table_header.addWidget(self.status_label)
        
        table_layout.addLayout(table_header)
        
        # Data table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                alternate-background-color: {COLORS['bg_light']};
            }}
        """)
        table_layout.addWidget(self.table)
        
        splitter.addWidget(table_container)
        
        # Set splitter sizes (60% chart, 40% table)
        splitter.setSizes([540, 360])
        
        main_layout.addWidget(splitter)
    
    def load_pdfs(self):
        """Load and parse PDF invoice files."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "PDF Rechnungen auswählen",
            "",
            "PDF Dateien (*.pdf)"
        )
        
        if not files:
            return
        
        new_expenses = []
        errors = []
        
        for file_path in files:
            try:
                expenses = self.parse_pdf(file_path)
                new_expenses.extend(expenses)
            except Exception as e:
                errors.append(f"{Path(file_path).name}: {str(e)}")
        
        if errors:
            QMessageBox.warning(
                self,
                "Parsing-Fehler",
                f"Fehler bei folgenden Dateien:\n\n" + "\n".join(errors)
            )
        
        if new_expenses:
            count = self.data_manager.add_expenses(new_expenses)
            self.status_label.setText(
                f"✓ {count} Rechnungen aus {len(files)} PDF(s) geladen"
            )
            self.status_label.setStyleSheet(f"color: {COLORS['kpi_positive']};")
            self.refresh_all()
        else:
            self.status_label.setText("Keine Rechnungsdaten in den PDFs gefunden")
            self.status_label.setStyleSheet(f"color: {COLORS['kpi_negative']};")
    
    def parse_pdf(self, file_path: str) -> list:
        """Parse a Revisage invoice PDF and extract net amount and date.
        
        Args:
            file_path: Path to the PDF file.
            
        Returns:
            List of expense dictionaries.
        """
        expenses = []
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                
                if not text:
                    continue
                
                # Extract invoice date (format: DD.MM.YYYY)
                date_match = re.search(r'Datum\s+(\d{2}\.\d{2}\.\d{4})', text)
                invoice_date = None
                
                if date_match:
                    try:
                        invoice_date = datetime.strptime(date_match.group(1), '%d.%m.%Y')
                    except ValueError:
                        pass
                
                # Fallback: find any date in DD.MM.YYYY format
                if not invoice_date:
                    date_match = re.search(r'\b(\d{2}\.\d{2}\.\d{4})\b', text)
                    if date_match:
                        try:
                            invoice_date = datetime.strptime(date_match.group(1), '%d.%m.%Y')
                        except ValueError:
                            invoice_date = datetime.now()
                    else:
                        invoice_date = datetime.now()
                
                # Extract NET amount (without VAT)
                # Strategy: 
                # 1. Try to find direct net amount from "% von XXX" pattern
                # 2. Fallback: Zwischensumme - MwSt. amount
                # 3. Fallback: Endsumme for invoices without tax
                
                net_amount = None
                vat_amount = None
                gross_amount = None
                
                # Method 1: Extract net amount directly from "% von [NET_AMOUNT] [VAT_AMOUNT]"
                # Pattern matches: "% von 921,43 175,07" where 921,43 is net and 175,07 is VAT
                vat_line_match = re.search(
                    r'%\s*von\s+(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})\s+(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
                    text
                )
                
                if vat_line_match:
                    # First amount after "% von" is the net amount
                    net_str = vat_line_match.group(1)
                    net_str = net_str.replace('.', '').replace(',', '.')
                    try:
                        net_amount = float(net_str)
                    except ValueError:
                        pass
                    
                    # Second amount is VAT (stored for reference)
                    vat_str = vat_line_match.group(2)
                    vat_str = vat_str.replace('.', '').replace(',', '.')
                    try:
                        vat_amount = float(vat_str)
                    except ValueError:
                        pass
                
                # Method 2: If direct extraction failed, calculate: Zwischensumme - VAT
                if not net_amount:
                    # Get Zwischensumme (gross amount)
                    zwischensumme_match = re.search(
                        r'Zwischensumme\s+(?:EUR\s+)?(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})', 
                        text
                    )
                    
                    if zwischensumme_match:
                        gross_str = zwischensumme_match.group(1)
                        gross_str = gross_str.replace('.', '').replace(',', '.')
                        try:
                            gross_amount = float(gross_str)
                        except ValueError:
                            pass
                    
                    # Get VAT amount if not already found
                    if not vat_amount:
                        # Pattern for VAT line: numbers ending with VAT amount
                        # Looking for pattern like "19,00 % von XXX YYY" where YYY is VAT
                        vat_match = re.search(
                            r'(?:19|20|7)[.,]00\s*%\s*von\s+[\d.,]+\s+(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
                            text
                        )
                        if vat_match:
                            vat_str = vat_match.group(1)
                            vat_str = vat_str.replace('.', '').replace(',', '.')
                            try:
                                vat_amount = float(vat_str)
                            except ValueError:
                                pass
                    
                    # Calculate net = gross - VAT
                    if gross_amount and vat_amount:
                        net_amount = gross_amount - vat_amount
                    elif gross_amount and not vat_amount:
                        # If no VAT found, check if invoice is VAT-exempt
                        if 'MwSt.' not in text and 'Steuercode' not in text:
                            net_amount = gross_amount
                
                # Method 3: Fallback to Endsumme for invoices without tax
                if not net_amount:
                    if 'MwSt.' not in text and 'Steuercode' not in text:
                        endsumme_match = re.search(
                            r'Endsumme\s+(?:EUR\s+)?(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})', 
                            text
                        )
                        if endsumme_match:
                            amount_str = endsumme_match.group(1)
                            amount_str = amount_str.replace('.', '').replace(',', '.')
                            try:
                                net_amount = float(amount_str)
                            except ValueError:
                                pass
                
                # Extract invoice number
                invoice_number = "Unbekannt"
                invoice_match = re.search(r'Belegnummer\s+(\d+-\d+)', text)
                if invoice_match:
                    invoice_number = invoice_match.group(1)
                
                # Extract vendor (basic)
                vendor = ""
                # Try to find company name at the top of invoice
                lines = text.split('\n')
                if lines:
                    vendor = lines[0].strip()[:50]  # First line, truncated
                
                # Add expense if valid
                if invoice_date and net_amount:
                    expenses.append({
                        'Date': invoice_date,
                        'Amount': net_amount,
                        'Description': f'Rechnung {invoice_number}',
                        'Source': Path(file_path).name,
                        'Vendor': vendor,
                        'Category': 'Uncategorized',
                        'Currency': 'EUR'
                    })
        
        return expenses
    
    def on_date_range_changed(self, start_date, end_date):
        """Handle date range filter changes."""
        self.current_start_date = start_date
        self.current_end_date = end_date
        
        # Reset comparison when primary range changes (unless comparison is updating it)
        if not self.comparison_enabled:
            self.refresh_all()
        else:
            self.refresh_all()
    
    def on_comparison_changed(self, enabled: bool, start1, end1, start2, end2, label1: str, label2: str):
        """Handle comparison mode changes."""
        self.comparison_enabled = enabled
        
        if enabled and start1 and end1 and start2 and end2:
            self.comparison_data = {
                'period1': (start1, end1),
                'period2': (start2, end2),
                'label1': label1,
                'label2': label2
            }
            
            # Update primary date range
            self.current_start_date = start1
            self.current_end_date = end1
            
            # Show comparison chart
            self.show_comparison_chart()
        else:
            self.comparison_data = None
            self.refresh_all()
    
    def show_comparison_chart(self):
        """Display comparison chart for two periods."""
        if not self.comparison_data:
            return
        
        period1 = self.comparison_data['period1']
        period2 = self.comparison_data['period2']
        label1 = self.comparison_data['label1']
        label2 = self.comparison_data['label2']
        
        # Get data for both periods
        df1 = self.data_manager.filter_by_date_range(period1[0], period1[1])
        df2 = self.data_manager.filter_by_date_range(period2[0], period2[1])
        
        # Aggregate by month for comparison
        if not df1.empty:
            df1['Month'] = df1['Date'].dt.month
            monthly1 = df1.groupby('Month')['Amount'].sum()
        else:
            monthly1 = pd.Series(dtype=float)
        
        if not df2.empty:
            df2['Month'] = df2['Date'].dt.month
            monthly2 = df2.groupby('Month')['Amount'].sum()
        else:
            monthly2 = pd.Series(dtype=float)
        
        # Update KPIs for primary period
        kpis = self.data_manager.calculate_kpis(period1[0], period1[1])
        self.kpi_panel.update_kpis(kpis)
        
        # Set comparison data on chart
        self.chart.set_comparison_data(monthly1, monthly2, label1, label2)
        
        # Force chart to comparison view
        chart_combo = self.chart.chart_type_combo
        chart_combo.blockSignals(True)
        chart_combo.setCurrentText("Periodenvergleich")
        chart_combo.blockSignals(False)
        self.chart.refresh_chart()
        
        # Update table with combined view
        self.show_comparison_table(df1, df2, label1, label2)
        
        # Update status
        total1 = df1['Amount'].sum() if not df1.empty else 0
        total2 = df2['Amount'].sum() if not df2.empty else 0
        diff = total1 - total2
        diff_pct = (diff / total2 * 100) if total2 > 0 else 0
        
        trend_icon = "↑" if diff > 0 else ("↓" if diff < 0 else "→")
        self.status_label.setText(
            f"📊 Vergleich: {label1} vs {label2} • Differenz: {trend_icon} €{abs(diff):,.2f} ({diff_pct:+.1f}%)".replace(',', 'X').replace('.', ',').replace('X', '.')
        )
        self.status_label.setStyleSheet(f"color: {COLORS['chart_orange']};")
    
    def show_comparison_table(self, df1: pd.DataFrame, df2: pd.DataFrame, label1: str, label2: str):
        """Show comparison data in table."""
        # Create monthly comparison
        month_names = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
        
        self.table.setRowCount(12)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Monat', label1, label2, 'Differenz'])
        
        # Aggregate by month
        monthly1 = {}
        monthly2 = {}
        
        if not df1.empty:
            df1_copy = df1.copy()
            df1_copy['Month'] = df1_copy['Date'].dt.month
            for m, amt in df1_copy.groupby('Month')['Amount'].sum().items():
                monthly1[m] = amt
        
        if not df2.empty:
            df2_copy = df2.copy()
            df2_copy['Month'] = df2_copy['Date'].dt.month
            for m, amt in df2_copy.groupby('Month')['Amount'].sum().items():
                monthly2[m] = amt
        
        for i, month in enumerate(range(1, 13)):
            # Month name
            self.table.setItem(i, 0, QTableWidgetItem(month_names[month-1]))
            
            # Period 1 amount
            amt1 = monthly1.get(month, 0)
            amt1_str = f"€{amt1:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if amt1 > 0 else "—"
            item1 = QTableWidgetItem(amt1_str)
            item1.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 1, item1)
            
            # Period 2 amount
            amt2 = monthly2.get(month, 0)
            amt2_str = f"€{amt2:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if amt2 > 0 else "—"
            item2 = QTableWidgetItem(amt2_str)
            item2.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 2, item2)
            
            # Difference
            if amt1 > 0 or amt2 > 0:
                diff = amt1 - amt2
                diff_str = f"€{diff:+,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            else:
                diff_str = "—"
            diff_item = QTableWidgetItem(diff_str)
            diff_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 3, diff_item)
        
        self.table.resizeColumnsToContents()
    
    def on_view_changed(self, view_name):
        """Handle view type changes."""
        self.update_display()
    
    def refresh_all(self):
        """Refresh all UI components with current data."""
        # Update KPIs
        kpis = self.data_manager.calculate_kpis(
            self.current_start_date, 
            self.current_end_date
        )
        self.kpi_panel.update_kpis(kpis)
        
        # Update display (chart and table)
        self.update_display()
        
        # Update Analytics (Phase A)
        self.update_analytics()
        
        # Update status
        total_count = len(self.data_manager.expenses_df)
        if total_count > 0:
            date_range = self.data_manager.get_date_range()
            if date_range[0] and date_range[1]:
                self.status_label.setText(
                    f"{total_count} Rechnungen • {date_range[0].strftime('%d.%m.%Y')} - {date_range[1].strftime('%d.%m.%Y')}"
                )
                self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
    
    def update_display(self):
        """Update chart and table based on current view."""
        if self.data_manager.expenses_df.empty:
            self.show_empty_state()
            return
        
        view_type = self.view_selector.current_view()
        
        if view_type == "Monatliche Summen":
            self.show_monthly_view()
        elif view_type == "Jährliche Summen":
            self.show_yearly_view()
        elif view_type == "Monatsvergleich":
            self.show_comparison_view()
        else:
            self.show_all_data()
    
    def show_empty_state(self):
        """Show empty state in chart and table."""
        self.table.setRowCount(0)
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(['Information'])
        self.table.setItem(0, 0, QTableWidgetItem("Keine Daten. Bitte PDF-Rechnungen laden."))
        
        # Chart will show empty message automatically
        self.chart.set_data(pd.DataFrame(), 'monthly')
    
    def show_monthly_view(self):
        """Show monthly totals."""
        monthly = self.data_manager.get_monthly_totals(
            self.current_start_date, 
            self.current_end_date
        )
        
        # Get raw data for advanced charts (heatmap, drill-down)
        if self.current_start_date and self.current_end_date:
            raw_data = self.data_manager.filter_by_date_range(
                self.current_start_date, self.current_end_date
            )
        else:
            raw_data = self.data_manager.expenses_df
        
        # Update table
        self.setup_table(['Monat', 'Betrag'], monthly, 
                        lambda row: [row['YearMonth'], f"€{row['Amount']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')])
        
        # Update chart with raw data for advanced features
        self.chart.set_data(monthly, 'monthly', raw_data)
    
    def show_yearly_view(self):
        """Show yearly totals."""
        yearly = self.data_manager.get_yearly_totals(
            self.current_start_date, 
            self.current_end_date
        )
        
        # Get raw data for advanced charts
        if self.current_start_date and self.current_end_date:
            raw_data = self.data_manager.filter_by_date_range(
                self.current_start_date, self.current_end_date
            )
        else:
            raw_data = self.data_manager.expenses_df
        
        # Update table
        self.setup_table(['Jahr', 'Betrag'], yearly,
                        lambda row: [str(int(row['Year'])), f"€{row['Amount']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')])
        
        # Update chart with raw data for drill-down
        self.chart.set_data(yearly, 'yearly', raw_data)
    
    def show_comparison_view(self):
        """Show month-over-month comparison."""
        comparison = self.data_manager.get_monthly_comparison()
        
        # Get raw data for advanced charts
        if self.current_start_date and self.current_end_date:
            raw_data = self.data_manager.filter_by_date_range(
                self.current_start_date, self.current_end_date
            )
        else:
            raw_data = self.data_manager.expenses_df
        
        # Update table with trend indicators
        self.table.setRowCount(len(comparison))
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Monat', 'Betrag', 'Änderung', 'Trend'])
        
        for i, (_, row) in enumerate(comparison.iterrows()):
            # Month
            self.table.setItem(i, 0, QTableWidgetItem(str(row['YearMonth'])))
            
            # Amount
            amount_str = f"€{row['Amount']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
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
            
            # Trend
            change_pct = row.get('ChangePercent', 0)
            if pd.notna(change_pct) and change_pct != 0:
                if change_pct > 0:
                    trend_str = f"↑ {change_pct:.1f}%"
                else:
                    trend_str = f"↓ {abs(change_pct):.1f}%"
            else:
                trend_str = "→ 0%"
            trend_item = QTableWidgetItem(trend_str)
            trend_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 3, trend_item)
        
        self.table.resizeColumnsToContents()
        
        # Update chart with raw data
        monthly = self.data_manager.get_monthly_totals(
            self.current_start_date, 
            self.current_end_date
        )
        self.chart.set_data(monthly, 'monthly', raw_data)
    
    def show_all_data(self):
        """Show all expense data."""
        if self.current_start_date and self.current_end_date:
            df = self.data_manager.filter_by_date_range(
                self.current_start_date, 
                self.current_end_date
            )
        else:
            df = self.data_manager.expenses_df.copy()
        
        # Store raw data for chart
        self.chart.raw_data = df
        
        # Update table
        self.table.setRowCount(len(df))
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Datum', 'Betrag', 'Beschreibung', 'Quelle', 'Kategorie'])
        
        for i, (_, row) in enumerate(df.iterrows()):
            self.table.setItem(i, 0, QTableWidgetItem(row['Date'].strftime('%d.%m.%Y')))
            
            amount_str = f"€{row['Amount']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            amount_item = QTableWidgetItem(amount_str)
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 1, amount_item)
            
            self.table.setItem(i, 2, QTableWidgetItem(row['Description']))
            self.table.setItem(i, 3, QTableWidgetItem(row['Source']))
            self.table.setItem(i, 4, QTableWidgetItem(row.get('Category', 'Uncategorized')))
        
        self.table.resizeColumnsToContents()
        
        # Update chart (scatter plot)
        self.chart.draw_scatter(df)
    
    # =========================================================================
    # Drill-Down Handling (Phase 2)
    # =========================================================================
    
    def handle_drill_down(self, level: str, data):
        """Handle drill-down navigation from charts.
        
        Args:
            level: Drill level ('year', 'month', 'back_to_year', 'back_to_overview')
            data: Context data for the drill level
        """
        if level == 'year':
            # Drill into a specific year - show monthly breakdown
            self.drill_year = int(data)
            self.show_year_detail(self.drill_year)
        
        elif level == 'month':
            # Drill into a specific month - show individual invoices
            self.drill_month = data
            self.show_month_detail(self.drill_month)
        
        elif level == 'back_to_year':
            # Go back to year view
            self.drill_month = None
            if self.drill_year:
                self.show_year_detail(self.drill_year)
            else:
                self.refresh_all()
        
        elif level == 'back_to_overview':
            # Reset to full overview
            self.drill_year = None
            self.drill_month = None
            self.chart.reset_drill_down()
            self.refresh_all()
    
    def show_year_detail(self, year: int):
        """Show monthly breakdown for a specific year."""
        # Filter data for this year
        df = self.data_manager.expenses_df[
            self.data_manager.expenses_df['Date'].dt.year == year
        ].copy()
        
        if df.empty:
            return
        
        # Monthly aggregation for the year
        df['YearMonth'] = df['Date'].dt.to_period('M').astype(str)
        monthly = df.groupby('YearMonth')['Amount'].sum().reset_index()
        
        # Update table
        self.setup_table(['Monat', 'Betrag'], monthly,
                        lambda row: [row['YearMonth'], 
                                    f"€{row['Amount']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')])
        
        # Update chart
        self.chart.set_data(monthly, 'monthly', df)
        
        # Update status
        total = df['Amount'].sum()
        self.status_label.setText(
            f"Jahr {year}: {len(df)} Rechnungen • Gesamt: €{total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        )
    
    def show_month_detail(self, year_month: str):
        """Show individual invoices for a specific month."""
        # Parse year-month
        try:
            period = pd.Period(year_month, freq='M')
            year, month = period.year, period.month
        except:
            return
        
        # Filter data for this month
        df = self.data_manager.expenses_df[
            (self.data_manager.expenses_df['Date'].dt.year == year) &
            (self.data_manager.expenses_df['Date'].dt.month == month)
        ].copy()
        
        if df.empty:
            return
        
        # Update table with individual invoices
        self.table.setRowCount(len(df))
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Datum', 'Betrag', 'Beschreibung', 'Quelle', 'Kategorie'])
        
        for i, (_, row) in enumerate(df.iterrows()):
            self.table.setItem(i, 0, QTableWidgetItem(row['Date'].strftime('%d.%m.%Y')))
            
            amount_str = f"€{row['Amount']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            amount_item = QTableWidgetItem(amount_str)
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 1, amount_item)
            
            self.table.setItem(i, 2, QTableWidgetItem(row['Description']))
            self.table.setItem(i, 3, QTableWidgetItem(row['Source']))
            self.table.setItem(i, 4, QTableWidgetItem(row.get('Category', 'Uncategorized')))
        
        self.table.resizeColumnsToContents()
        
        # Update chart to scatter for this month
        self.chart.draw_scatter(df)
        
        # Update status
        total = df['Amount'].sum()
        self.status_label.setText(
            f"{year_month}: {len(df)} Rechnungen • Gesamt: €{total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        )
    
    def setup_table(self, headers: list, df: pd.DataFrame, row_formatter):
        """Setup table with headers and data.
        
        Args:
            headers: List of column headers.
            df: DataFrame with data.
            row_formatter: Function to format each row.
        """
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        for i, (_, row) in enumerate(df.iterrows()):
            values = row_formatter(row)
            for j, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if j == 1:  # Amount column - right align
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(i, j, item)
        
        self.table.resizeColumnsToContents()
        
        # Stretch last column
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(len(headers) - 1, QHeaderView.ResizeMode.Stretch)
    
    def clear_data(self):
        """Clear all data after confirmation."""
        reply = QMessageBox.question(
            self,
            "Daten löschen",
            "Möchten Sie wirklich alle Daten löschen?\nDiese Aktion kann nicht rückgängig gemacht werden.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.data_manager.clear_data()
            self.refresh_all()
            self.status_label.setText("Alle Daten wurden gelöscht")
            self.status_label.setStyleSheet(f"color: {COLORS['text_muted']};")
    
    # =========================================================================
    # Search and Filter (Phase 3)
    # =========================================================================
    
    def on_search_changed(self, query: str, category: str, min_amount: float, max_amount: float):
        """Handle search/filter changes."""
        # Apply search filters
        df = self.data_manager.search_expenses(
            query=query,
            start_date=self.current_start_date,
            end_date=self.current_end_date,
            category=category if category != 'Alle Kategorien' else None,
            min_amount=min_amount if min_amount > 0 else None,
            max_amount=max_amount if max_amount > 0 and max_amount < 9999999 else None
        )
        
        # Update table with filtered results
        self.show_filtered_data(df)
        
        # Update status
        total = df['Amount'].sum() if not df.empty else 0
        self.status_label.setText(
            f"🔍 {len(df)} Ergebnisse • Summe: €{total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        )
        self.status_label.setStyleSheet(f"color: {COLORS['primary']};")
    
    def show_filtered_data(self, df: pd.DataFrame):
        """Show filtered expense data with editable categories."""
        if df.empty:
            self.table.setRowCount(1)
            self.table.setColumnCount(1)
            self.table.setHorizontalHeaderLabels(['Information'])
            self.table.setItem(0, 0, QTableWidgetItem("Keine Ergebnisse gefunden"))
            return
        
        # Setup table with category column
        self.table.setRowCount(len(df))
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['Datum', 'Betrag', 'Beschreibung', 'Kategorie', 'Lieferant', 'Quelle'])
        
        for i, (_, row) in enumerate(df.iterrows()):
            # Date
            self.table.setItem(i, 0, QTableWidgetItem(row['Date'].strftime('%d.%m.%Y')))
            
            # Amount
            amount_str = f"€{row['Amount']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            amount_item = QTableWidgetItem(amount_str)
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 1, amount_item)
            
            # Description
            self.table.setItem(i, 2, QTableWidgetItem(row['Description']))
            
            # Category - with ComboBox for editing
            category_combo = CategoryEditorDialog.create_category_combo()
            category_combo.setCurrentText(row.get('Category', 'Uncategorized'))
            expense_id = row.get('ID', '')
            category_combo.currentTextChanged.connect(
                lambda cat, eid=expense_id: self.on_category_changed(eid, cat)
            )
            self.table.setCellWidget(i, 3, category_combo)
            
            # Vendor
            self.table.setItem(i, 4, QTableWidgetItem(row.get('Vendor', '')))
            
            # Source
            self.table.setItem(i, 5, QTableWidgetItem(row['Source']))
        
        self.table.resizeColumnsToContents()
        
        # Adjust column widths
        self.table.setColumnWidth(2, 200)  # Description
        self.table.setColumnWidth(3, 140)  # Category
    
    def on_category_changed(self, expense_id: str, new_category: str):
        """Handle category change from table."""
        if expense_id:
            self.data_manager.update_expense_category(expense_id, new_category)
    
    # =========================================================================
    # Export Functions (Phase 3)
    # =========================================================================
    
    def export_to_csv(self):
        """Export current data to CSV file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "CSV exportieren",
            f"einnahmen_export_{datetime.now().strftime('%Y%m%d')}.csv",
            "CSV Dateien (*.csv)"
        )
        
        if filepath:
            success = self.data_manager.export_to_csv(
                filepath,
                self.current_start_date,
                self.current_end_date
            )
            
            if success:
                QMessageBox.information(
                    self, "Export erfolgreich",
                    f"Daten wurden erfolgreich exportiert:\n{filepath}"
                )
            else:
                QMessageBox.warning(
                    self, "Export fehlgeschlagen",
                    "Die Daten konnten nicht exportiert werden."
                )
    
    def export_to_excel(self):
        """Export current data to Excel file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Excel exportieren",
            f"einnahmen_export_{datetime.now().strftime('%Y%m%d')}.xlsx",
            "Excel Dateien (*.xlsx)"
        )
        
        if filepath:
            success = self.data_manager.export_to_excel(
                filepath,
                self.current_start_date,
                self.current_end_date
            )
            
            if success:
                QMessageBox.information(
                    self, "Export erfolgreich",
                    f"Daten wurden erfolgreich exportiert:\n{filepath}"
                )
            else:
                QMessageBox.warning(
                    self, "Export fehlgeschlagen",
                    "Die Daten konnten nicht exportiert werden.\n\n"
                    "Hinweis: Für Excel-Export wird 'openpyxl' benötigt.\n"
                    "Installation: pip install openpyxl"
                )
    
    def export_to_pdf(self):
        """Export current data to PDF report."""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "PDF exportieren",
            f"einnahmen_report_{datetime.now().strftime('%Y%m%d')}.pdf",
            "PDF Dateien (*.pdf)"
        )
        
        if filepath:
            success = self.data_manager.export_to_pdf(
                filepath,
                self.current_start_date,
                self.current_end_date
            )
            
            if success:
                QMessageBox.information(
                    self, "Export erfolgreich",
                    f"PDF-Report wurde erstellt:\n{filepath}"
                )
            else:
                QMessageBox.warning(
                    self, "Export fehlgeschlagen",
                    "Der PDF-Report konnte nicht erstellt werden.\n\n"
                    "Hinweis: Für PDF-Export wird 'reportlab' benötigt.\n"
                    "Installation: pip install reportlab"
                )
    
    # =========================================================================
    # Analytics Engine Methods (Phase A)
    # =========================================================================
    
    def update_analytics(self, method: str = "combined"):
        """Update forecasts and recommendations using Analytics Engine.
        
        Args:
            method: Forecast method ('combined', 'linear', 'exponential', 
                   'moving_average', 'growth_rate')
        """
        # Get filtered data
        if self.current_start_date and self.current_end_date:
            data = self.data_manager.filter_by_date_range(
                self.current_start_date, self.current_end_date
            )
        else:
            data = self.data_manager.expenses_df
        
        if data.empty:
            self.analytics_panel.update_forecast({})
            self.analytics_panel.update_recommendations([])
            return
        
        # Initialize Forecast Engine
        try:
            forecast_engine = ForecastEngine(data)
            
            # Get forecast based on method
            if method == "combined":
                forecast = forecast_engine.combined_forecast(periods=6)
            elif method == "linear":
                forecast = forecast_engine.linear_regression_forecast(periods=6)
            elif method == "exponential":
                forecast = forecast_engine.exponential_smoothing_forecast(periods=6)
            elif method == "moving_average":
                forecast = forecast_engine.moving_average_forecast(periods=6)
            elif method == "growth_rate":
                forecast = forecast_engine.growth_rate_forecast(periods=6)
            else:
                forecast = forecast_engine.combined_forecast(periods=6)
            
            # Store forecast for chart overlay
            self.current_forecast = forecast
            
            # Update panel
            self.analytics_panel.update_forecast(forecast)
            
        except Exception as e:
            print(f"Forecast error: {e}")
            self.current_forecast = None
            self.analytics_panel.update_forecast({
                'method': 'Fehler',
                'interpretation': {'message': str(e)}
            })
        
        # Generate Recommendations
        try:
            recommendation_engine = RecommendationEngine(revenue_data=data)
            recommendations = recommendation_engine.analyze_all()
            
            # Convert to dict list for UI
            rec_dicts = [r.to_dict() for r in recommendations]
            self.analytics_panel.update_recommendations(rec_dicts)
            
        except Exception as e:
            print(f"Recommendation error: {e}")
            self.analytics_panel.update_recommendations([])
    
    def on_forecast_method_changed(self, method: str):
        """Handle forecast method change from UI.
        
        Args:
            method: Method identifier from AnalyticsPanel
        """
        self.update_analytics(method)


def main():
    """Application entry point."""
    # Enable High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Consistent look across platforms
    
    # Set application metadata (for Desktop App)
    app.setApplicationName("Rechnungsanalyse-Tool")
    app.setApplicationVersion("3.1.0")
    app.setOrganizationName("Rechnungsanalyse")
    
    window = ExpenseTrackerApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

