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
    AnalyticsPanel, ManualEntryDialog
)
from charts import ExpenseChart

# Analytics Engine (Phase A)
from analytics import ForecastEngine, RecommendationEngine


class ExpenseTrackerApp(QMainWindow):
    """Main application window with Business Intelligence Dashboard."""
    
    APP_NAME = "Business Intelligence Suite"
    APP_VERSION = "3.2.1"  # Marketing Dashboard entfernt (noch nicht implementiert)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{self.APP_NAME} v{self.APP_VERSION}")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 700)
        
        # Apply dark theme
        self.setStyleSheet(MAIN_STYLESHEET)
        apply_matplotlib_style()
        
        # Initialize data managers (separate for revenue and expenses)
        self.data_manager = DataManager()  # Revenue data
        self.expenses_data_manager = DataManager(
            data_dir=Path(__file__).parent / "data",
            data_file="expenses_costs.json"  # Separate file for expenses
        )
        
        # Current filter state
        self.current_start_date = None
        self.current_end_date = None
        
        # Comparison state
        self.comparison_enabled = False
        self.comparison_data = None  # Dict with comparison ranges and labels
        
        # Drill-down state
        self.drill_year = None
        self.drill_month = None
        
        # Table edit state
        self._current_table_view = 'aggregated'
        self._table_expense_ids = []
        
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
        
        # App title
        app_title = QLabel("🏢 Business Suite")
        app_title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {COLORS['text_secondary']};
        """)
        header_layout.addWidget(app_title)
        
        # Dashboard selector dropdown
        self.dashboard_selector = QComboBox()
        self.dashboard_selector.addItems([
            "📊 Einnahmenanalyse",
            "💸 Ausgabenanalyse",
            "🔄 Cross-Dashboard"
        ])
        # Hinweis: Marketing-Analyse vorübergehend deaktiviert (noch nicht implementiert)
        self.dashboard_selector.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_elevated']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['primary']};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 16px;
                font-weight: 600;
                min-width: 220px;
            }}
            QComboBox:hover {{
                border-color: {COLORS['primary_light']};
                background-color: {COLORS['bg_light']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {COLORS['primary']};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['bg_medium']};
                color: {COLORS['text_primary']};
                selection-background-color: {COLORS['primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 8px 12px;
                min-height: 30px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: {COLORS['bg_elevated']};
            }}
        """)
        self.dashboard_selector.currentTextChanged.connect(self.on_dashboard_changed)
        header_layout.addWidget(self.dashboard_selector)
        
        header_layout.addStretch()
        
        # Dynamic action button (changes per dashboard)
        self.action_btn = QPushButton("📁 PDF Laden")
        self.action_btn.setMinimumWidth(140)
        self.action_btn.clicked.connect(self.on_action_button_clicked)
        header_layout.addWidget(self.action_btn)
        
        self.manual_entry_btn = QPushButton("✏️ Manuell eingeben")
        self.manual_entry_btn.setMinimumWidth(160)
        self.manual_entry_btn.clicked.connect(self.open_manual_entry)
        header_layout.addWidget(self.manual_entry_btn)
        
        self.clear_btn = QPushButton("🗑️ Daten löschen")
        self.clear_btn.setProperty("class", "secondary")
        self.clear_btn.setMinimumWidth(140)
        self.clear_btn.clicked.connect(self.clear_data)
        header_layout.addWidget(self.clear_btn)
        
        main_layout.addLayout(header_layout)
        
        # Store current dashboard
        self.current_dashboard = "revenue"
        
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
        # Enable double-click to edit
        self.table.doubleClicked.connect(self.on_table_double_click)
        table_layout.addWidget(self.table)
        
        splitter.addWidget(table_container)
        
        # Set splitter sizes (60% chart, 40% table)
        splitter.setSizes([540, 360])
        
        main_layout.addWidget(splitter)
    
    def load_pdfs(self):
        """Load and parse PDF invoice files."""
        # Determine which dashboard we're on
        is_expenses = self.current_dashboard == "expenses"
        dashboard_label = "Ausgaben" if is_expenses else "Einnahmen"
        
        files, _ = QFileDialog.getOpenFileNames(
            self,
            f"PDF {dashboard_label}-Rechnungen auswählen",
            "",
            "PDF Dateien (*.pdf)"
        )
        
        if not files:
            return
        
        new_expenses = []
        errors = []
        
        for file_path in files:
            try:
                # Parse with dashboard type for tagging
                expenses = self.parse_pdf(file_path, dashboard_type=self.current_dashboard)
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
            # Use appropriate data manager
            if is_expenses:
                count = self.expenses_data_manager.add_expenses(new_expenses)
                self.status_label.setText(
                    f"✓ {count} Ausgaben aus {len(files)} PDF(s) geladen"
                )
                self.refresh_expenses_dashboard()
            else:
                count = self.data_manager.add_expenses(new_expenses)
                self.status_label.setText(
                    f"✓ {count} Einnahmen aus {len(files)} PDF(s) geladen"
                )
                self.refresh_all()
            
            self.status_label.setStyleSheet(f"color: {COLORS['kpi_positive']};")
        else:
            self.status_label.setText("Keine Rechnungsdaten in den PDFs gefunden")
            self.status_label.setStyleSheet(f"color: {COLORS['kpi_negative']};")
    
    # Extended keywords for net amount detection (various invoice formats)
    # Priority order: More specific keywords first, then general ones
    NET_AMOUNT_KEYWORDS_PRIORITY = [
        # HIGH PRIORITY: Keywords with "Gesamt/Total" context (more likely to be the final net amount)
        r'Gesamt[\s-]*netto',
        r'Gesamtbetrag[\s-]*netto',
        r'Gesamtwert[\s-]*netto',
        r'Gesamt[\s-]*Nettopreis',
        r'Netto[\s-]*Gesamt',
        r'Total[\s-]*net',
        r'Net[\s-]*total',
        r'Total[\s-]*excl\.?\s*VAT',
        r'Gesamt\s*ohne\s*MwSt',
        r'Gesamt\s*ohne\s*USt',
        
        # MEDIUM PRIORITY: Standard net amount keywords
        r'Nettobetrag',
        r'Netto[\s-]*Betrag',
        r'Nettosumme',
        r'Netto[\s-]*Summe',
        r'Nettowert',
        r'Summe[\s-]*netto',
        r'Betrag[\s-]*netto',
        r'Wert[\s-]*netto',
        r'Zwischensumme[\s-]*netto',
        r'Zw\.?[\s-]*Summe[\s-]*netto',
        r'Rechnungsbetrag[\s-]*netto',
        r'Rechnungssumme[\s-]*netto',
        
        # German: Without VAT/Tax keywords
        r'Betrag\s*ohne\s*MwSt',
        r'Summe\s*ohne\s*MwSt',
        r'ohne\s*Umsatzsteuer',
        r'exkl\.?\s*MwSt',
        r'ex\.?\s*MwSt',
        r'exkl\.?\s*USt',
        r'ohne\s*USt',
        r'Steuerbasis',
        
        # English: Net amount keywords
        r'Net\s*amount',
        r'Net\s*sum',
        r'Net\s*value',
        r'Amount\s*net',
        r'Value\s*net',
        r'Subtotal',
        r'Sub[\s-]*total',
        
        # English: Excluding VAT keywords
        r'Amount\s*excl\.?\s*VAT',
        r'Excluding\s*VAT',
        r'Amount\s*exclusive\s*VAT',
        r'Exclusive\s*of\s*VAT',
        r'VAT\s*excluded',
        r'Net\s*of\s*VAT',
        r'Pre[\s-]*tax\s*amount',
        r'Before\s*tax',
        r'Base\s*amount',
        r'Tax\s*base',
        r'excl\.?\s*VAT',
        r'ex\.?\s*VAT',
        r'EX[\s-]*VAT',
        r'before\s*VAT',
        r'excl\.?\s*tax',
        r'before\s*tax',
        r'pre[\s-]*tax',
        r'amount\s*ex\s*tax',
        
        # LOW PRIORITY: Generic keywords (might match single items)
        r'Netto',
        r'Warenwert',
        r'Zwischensumme',
    ]
    
    # Patterns to EXCLUDE (single item prices, not totals)
    EXCLUDE_PATTERNS = [
        r'Einzelpreis',
        r'Stückpreis',
        r'Preis\s*pro',
        r'je\s*Stück',
        r'Unit\s*price',
        r'Price\s*per',
        r'Menge',
        r'Qty',
        r'Anzahl',
    ]
    
    def parse_pdf(self, file_path: str, dashboard_type: str = 'revenue') -> list:
        """Parse an invoice PDF and extract net amount and date.
        
        Supports various invoice formats with extended keyword detection.
        
        Args:
            file_path: Path to the PDF file.
            dashboard_type: 'revenue' or 'expenses' to tag the entry.
            
        Returns:
            List of expense dictionaries.
        """
        expenses = []
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                
                if not text:
                    continue
                
                # Extract invoice date (multiple formats)
                invoice_date = self._extract_invoice_date(text)
                if not invoice_date:
                    invoice_date = datetime.now()
                
                # Extract NET amount using the extended keyword-based extraction
                net_amount = self._extract_net_amount(text)
                
                # Fallback: Try to extract from Endsumme if no VAT info present
                if not net_amount:
                    if 'MwSt' not in text and 'USt' not in text and 'VAT' not in text:
                        endsumme_match = re.search(
                            r'(?:Endsumme|Gesamtsumme|Total|Summe)\s*[:\s€]*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})', 
                            text, re.IGNORECASE
                        )
                        if endsumme_match:
                            net_amount = self._parse_amount(endsumme_match.group(1))
                
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
                        'Currency': 'EUR',
                        'DashboardType': dashboard_type,  # Track which dashboard this belongs to
                        'PeriodType': 'monthly'  # PDF imports are treated as monthly
                    })
        
        return expenses
    
    def _extract_invoice_date(self, text: str) -> datetime:
        """Extract invoice date from text using multiple patterns.
        
        Args:
            text: Invoice text content.
            
        Returns:
            datetime object or None if not found.
        """
        # Pattern 1: "Datum" + date
        date_patterns = [
            (r'(?:Rechnungs)?[Dd]atum[:\s]+(\d{2})[./](\d{2})[./](\d{4})', '%d.%m.%Y'),
            (r'(?:Invoice\s*)?[Dd]ate[:\s]+(\d{2})[./](\d{2})[./](\d{4})', '%d.%m.%Y'),
            (r'(\d{2})[./](\d{2})[./](\d{4})', '%d.%m.%Y'),  # Fallback: any date
            (r'(\d{4})-(\d{2})-(\d{2})', '%Y-%m-%d'),  # ISO format
        ]
        
        for pattern, date_format in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if date_format == '%d.%m.%Y':
                        date_str = f"{match.group(1)}.{match.group(2)}.{match.group(3)}"
                    else:
                        date_str = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                    return datetime.strptime(date_str, date_format)
                except ValueError:
                    continue
        
        return None
    
    def _extract_net_amount(self, text: str) -> float:
        """Extract net amount using extended keyword matching.
        
        Uses priority-based keyword search with context analysis.
        Excludes single-item prices and prefers totals.
        
        Args:
            text: Invoice text content.
            
        Returns:
            Net amount as float or None.
        """
        # Normalize text for better matching
        text_clean = text.replace('\n', ' ').replace('\r', ' ')
        
        # Amount pattern: supports both 1.234,56 (German) and 1,234.56 (English)
        amount_pattern = r'(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})'
        
        candidates = []
        
        # Method 1: Priority keyword-based extraction
        for priority, keyword in enumerate(self.NET_AMOUNT_KEYWORDS_PRIORITY):
            # Search with context: keyword followed by optional separators and amount
            pattern = rf'{keyword}\s*[:\s€$]*(?:EUR|USD|CHF)?\s*{amount_pattern}'
            
            for match in re.finditer(pattern, text_clean, re.IGNORECASE):
                amount_str = match.group(1)
                
                # Get context around the match to check for exclusions
                start = max(0, match.start() - 50)
                end = min(len(text_clean), match.end() + 20)
                context = text_clean[start:end]
                
                # Check if this looks like a single item price (exclude)
                is_excluded = False
                for exclude in self.EXCLUDE_PATTERNS:
                    if re.search(exclude, context, re.IGNORECASE):
                        is_excluded = True
                        break
                
                if not is_excluded:
                    amount = self._parse_amount(amount_str)
                    if amount and amount > 0:
                        candidates.append({
                            'amount': amount,
                            'priority': priority,
                            'keyword': keyword,
                            'context': context.strip()
                        })
        
        # Method 2: Look for amount after "Netto" anywhere (case-insensitive)
        netto_pattern = rf'\bnetto\b[^0-9]*{amount_pattern}'
        for match in re.finditer(netto_pattern, text_clean, re.IGNORECASE):
            amount = self._parse_amount(match.group(1))
            if amount and amount > 0:
                candidates.append({
                    'amount': amount,
                    'priority': 100,  # Lower priority
                    'keyword': 'Netto (generic)',
                    'context': ''
                })
        
        # Method 3: Original "% von" pattern (Revisage format)
        vat_line_match = re.search(
            r'%\s*von\s+(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})\s+(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
            text_clean
        )
        if vat_line_match:
            amount = self._parse_amount(vat_line_match.group(1))
            if amount and amount > 0:
                candidates.append({
                    'amount': amount,
                    'priority': 5,  # High priority for specific format
                    'keyword': '% von pattern',
                    'context': ''
                })
        
        # Method 4: Look for "Zwischensumme" or "Subtotal" patterns
        for pattern in [r'Zwischensumme\s*[:\s€]*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
                        r'Subtotal\s*[:\s€$]*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})']:
            match = re.search(pattern, text_clean, re.IGNORECASE)
            if match:
                amount = self._parse_amount(match.group(1))
                if amount and amount > 0:
                    candidates.append({
                        'amount': amount,
                        'priority': 20,
                        'keyword': 'Zwischensumme/Subtotal',
                        'context': ''
                    })
        
        # Select best candidate (lowest priority number = highest priority)
        if candidates:
            # Sort by priority (ascending), then by amount (descending for tie-breaker)
            candidates.sort(key=lambda x: (x['priority'], -x['amount']))
            best = candidates[0]
            print(f"[PDF Parser] Found net amount: {best['amount']:.2f} using '{best['keyword']}'")
            return best['amount']
        
        return None
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float, handling German and English formats.
        
        Args:
            amount_str: Amount string like "1.234,56" or "1,234.56"
            
        Returns:
            Float amount or None if parsing fails.
        """
        if not amount_str:
            return None
        
        try:
            # Determine format: German (1.234,56) or English (1,234.56)
            # Count dots and commas
            dots = amount_str.count('.')
            commas = amount_str.count(',')
            
            if commas == 1 and dots >= 1:
                # German format: 1.234,56 -> remove dots, replace comma with dot
                amount_str = amount_str.replace('.', '').replace(',', '.')
            elif dots == 1 and commas >= 1:
                # English format: 1,234.56 -> remove commas
                amount_str = amount_str.replace(',', '')
            elif commas == 1 and dots == 0:
                # German format without thousands: 234,56
                amount_str = amount_str.replace(',', '.')
            elif dots == 1 and commas == 0:
                # English format without thousands: 234.56
                pass  # Already correct
            
            return float(amount_str)
        except ValueError:
            return None
    
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
        # Mark as aggregated view (no direct editing)
        self._current_table_view = 'aggregated'
        self._table_expense_ids = []
        
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
        # Mark as aggregated view (no direct editing)
        self._current_table_view = 'aggregated'
        self._table_expense_ids = []
        
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
        # Mark as aggregated view (no direct editing)
        self._current_table_view = 'aggregated'
        self._table_expense_ids = []
        
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
        
        # Store current view type for double-click handling
        self._current_table_view = 'all_data'
        self._table_expense_ids = []
        
        # Update table
        self.table.setRowCount(len(df))
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Datum', 'Betrag', 'Beschreibung', 'Quelle', 'Kategorie'])
        
        for i, (_, row) in enumerate(df.iterrows()):
            # Store expense ID for this row
            self._table_expense_ids.append(row.get('ID', ''))
            
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
        # Mark as editable view
        self._current_table_view = 'all_data'
        self._table_expense_ids = []
        
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
            # Store expense ID for this row
            self._table_expense_ids.append(row.get('ID', ''))
            
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
        """Clear all data for the current dashboard."""
        if self.current_dashboard == "revenue":
            reply = QMessageBox.question(
                self,
                "Einnahmen-Daten loeschen",
                "Moechten Sie wirklich ALLE Einnahmen-Daten loeschen?\n\n"
                "Diese Aktion kann nicht rueckgaengig gemacht werden.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.data_manager.clear_data()
                self.refresh_all()
                self.status_label.setText("Alle Einnahmen-Daten wurden geloescht")
                self.status_label.setStyleSheet(f"color: {COLORS['text_muted']};")
                
        elif self.current_dashboard == "expenses":
            reply = QMessageBox.question(
                self,
                "Ausgaben-Daten loeschen",
                "Moechten Sie wirklich ALLE Ausgaben-Daten loeschen?\n\n"
                "Diese Aktion kann nicht rueckgaengig gemacht werden.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.expenses_data_manager.clear_data()
                self.refresh_expenses_dashboard()
                self.status_label.setText("Alle Ausgaben-Daten wurden geloescht")
                self.status_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        else:
            QMessageBox.information(
                self, "Information",
                "Fuer dieses Dashboard ist die Loeschfunktion noch nicht verfuegbar."
            )
    
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
        # Mark as editable view
        self._current_table_view = 'all_data'
        self._table_expense_ids = []
        
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
            # Store expense ID for this row
            expense_id = row.get('ID', '')
            self._table_expense_ids.append(expense_id)
            
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
    # Analytics Engine Methods (Phase A: Extended Horizons)
    # =========================================================================
    
    def update_analytics(self, method: str = "combined"):
        """Update forecasts and recommendations using Analytics Engine.
        
        Calculates extended forecast horizons:
        - Next month
        - Next quarter (3 months)
        - Next year (12 months)
        - 2 years (24 months)
        - 3 years (36 months)
        
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
            
            # Get forecast with extended horizons
            forecast = forecast_engine.forecast_with_horizons(method=method)
            
            # Store forecast for chart overlay
            self.current_forecast = forecast
            
            # Update panel with extended horizons
            self.analytics_panel.update_forecast(forecast)
            
        except Exception as e:
            print(f"Forecast error: {e}")
            import traceback
            traceback.print_exc()
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
    
    # =========================================================================
    # Dashboard Navigation
    # =========================================================================
    
    def on_dashboard_changed(self, dashboard_name: str):
        """Handle dashboard selection change.
        
        Args:
            dashboard_name: Selected dashboard from dropdown
        """
        dashboard_map = {
            "📊 Einnahmenanalyse": "revenue",
            "💸 Ausgabenanalyse": "expenses",
            "🔄 Cross-Dashboard": "cross"
        }
        
        self.current_dashboard = dashboard_map.get(dashboard_name, "revenue")
        
        # Update action button based on dashboard
        action_labels = {
            "revenue": "📁 PDF Laden",
            "expenses": "📁 PDF Laden",
            "cross": "🔄 Analyse aktualisieren"
        }
        self.action_btn.setText(action_labels.get(self.current_dashboard, "📁 PDF Laden"))
        
        # Show appropriate content
        if self.current_dashboard == "revenue":
            self.show_revenue_dashboard()
        elif self.current_dashboard == "expenses":
            self.show_expenses_dashboard()
        elif self.current_dashboard == "cross":
            self.show_cross_dashboard()
    
    def on_action_button_clicked(self):
        """Handle action button click based on current dashboard."""
        if self.current_dashboard == "revenue":
            self.load_pdfs()
        elif self.current_dashboard == "expenses":
            self.load_pdfs()  # Will be separate expense PDFs later
        elif self.current_dashboard == "cross":
            self.refresh_all()
    
    def open_manual_entry(self):
        """Open dialog for manual data entry."""
        dialog = ManualEntryDialog(self, dashboard_type=self.current_dashboard)
        dialog.entry_saved.connect(self.on_manual_entry_saved)
        dialog.exec()
    
    def on_manual_entry_saved(self, entry_data: dict):
        """Handle saved manual entry (new or updated).
        
        Args:
            entry_data: Dictionary with entry data from dialog
        """
        is_update = entry_data.pop('_is_update', False)
        is_expenses = self.current_dashboard == "expenses"
        
        # Select appropriate data manager
        dm = self.expenses_data_manager if is_expenses else self.data_manager
        label = "Ausgabe" if is_expenses else "Einnahme"
        
        # Add DashboardType tag
        entry_data['DashboardType'] = self.current_dashboard
        
        if is_update:
            # Update existing entry
            expense_id = entry_data.get('ID')
            success = dm.update_expense(expense_id, entry_data)
            
            if success:
                self.status_label.setText(
                    f"✓ {label} aktualisiert: {entry_data['Description']}"
                )
                self.status_label.setStyleSheet(f"color: {COLORS['kpi_positive']};")
                if is_expenses:
                    self.refresh_expenses_dashboard()
                else:
                    self.refresh_all()
            else:
                self.status_label.setText("Fehler beim Aktualisieren")
                self.status_label.setStyleSheet(f"color: {COLORS['kpi_negative']};")
        else:
            # Add new entry
            count = dm.add_expenses([entry_data])
            
            if count > 0:
                self.status_label.setText(
                    f"✓ {label} gespeichert: {entry_data['Description']}"
                )
                self.status_label.setStyleSheet(f"color: {COLORS['kpi_positive']};")
                if is_expenses:
                    self.refresh_expenses_dashboard()
                else:
                    self.refresh_all()
            else:
                self.status_label.setText(f"Fehler beim Speichern der {label}")
                self.status_label.setStyleSheet(f"color: {COLORS['kpi_negative']};")
    
    def on_entry_deleted(self, expense_id: str):
        """Handle entry deletion.
        
        Args:
            expense_id: ID of the expense to delete
        """
        is_expenses = self.current_dashboard == "expenses"
        dm = self.expenses_data_manager if is_expenses else self.data_manager
        
        success = dm.delete_expense(expense_id)
        
        if success:
            self.status_label.setText("✓ Eintrag gelöscht")
            self.status_label.setStyleSheet(f"color: {COLORS['chart_orange']};")
            if is_expenses:
                self.refresh_expenses_dashboard()
            else:
                self.refresh_all()
        else:
            self.status_label.setText("Fehler beim Löschen")
            self.status_label.setStyleSheet(f"color: {COLORS['kpi_negative']};")
    
    def on_table_double_click(self, index):
        """Handle double-click on table row to edit entry.
        
        Args:
            index: QModelIndex of clicked cell
        """
        # Only allow editing in 'all_data' view
        current_view = getattr(self, '_current_table_view', 'aggregated')
        if current_view != 'all_data':
            # Show hint for aggregated views
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Hinweis",
                "Zum Bearbeiten einzelner Einträge bitte zur Ansicht 'Alle Daten' wechseln."
            )
            return
        
        row = index.row()
        expense_ids = getattr(self, '_table_expense_ids', [])
        
        if not expense_ids or row >= len(expense_ids):
            return
        
        expense_id = expense_ids[row]
        
        if not expense_id:
            return
        
        # Get full expense data from appropriate data manager
        is_expenses = self.current_dashboard == "expenses"
        dm = self.expenses_data_manager if is_expenses else self.data_manager
        expense_data = dm.get_expense_by_id(expense_id)
        
        if expense_data:
            # Open edit dialog
            dialog = ManualEntryDialog(
                self, 
                dashboard_type=self.current_dashboard,
                existing_data=expense_data
            )
            dialog.entry_saved.connect(self.on_manual_entry_saved)
            dialog.entry_deleted.connect(self.on_entry_deleted)
            dialog.exec()
    
    def show_revenue_dashboard(self):
        """Show revenue analysis dashboard (current implementation)."""
        # Reset KPI label to revenue
        if hasattr(self, 'kpi_panel') and hasattr(self.kpi_panel, 'total_card'):
            self.kpi_panel.total_card.title_label.setText("GESAMTEINNAHMEN")
        
        # Show analytics panel for revenue dashboard
        if hasattr(self, 'analytics_panel'):
            self.analytics_panel.setVisible(True)
        
        # This is already the default view
        self.refresh_all()
        self.status_label.setText("Einnahmenanalyse aktiv")
    
    def show_expenses_dashboard(self):
        """Show expenses analysis dashboard (without analytics panel)."""
        try:
            self.status_label.setText("Ausgaben-Analyse aktiv")
            self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
            self.refresh_expenses_dashboard()
            
        except Exception as e:
            print(f"ERROR in show_expenses_dashboard: {e}")
            import traceback
            traceback.print_exc()
            self.status_label.setText(f"Fehler: {str(e)}")
    
    def refresh_expenses_dashboard(self):
        """Refresh the expenses dashboard with current data (no analytics)."""
        try:
            if not hasattr(self, 'expenses_data_manager'):
                return
            
            # Calculate KPIs for expenses
            kpis = self.expenses_data_manager.calculate_kpis(None, None)
            
            if hasattr(self, 'kpi_panel'):
                # Update KPI labels for expenses
                if hasattr(self.kpi_panel, 'total_card'):
                    self.kpi_panel.total_card.title_label.setText("GESAMTAUSGABEN")
                self.kpi_panel.update_kpis(kpis)
            
            # Update chart and table
            self.update_expenses_display()
            
            # Hide analytics panel for expenses (only revenue has forecasting)
            if hasattr(self, 'analytics_panel'):
                self.analytics_panel.setVisible(False)
            
            # Update status
            total_count = len(self.expenses_data_manager.expenses_df) if not self.expenses_data_manager.expenses_df.empty else 0
            if total_count > 0:
                date_range = self.expenses_data_manager.get_date_range()
                if date_range and date_range[0] and date_range[1]:
                    self.status_label.setText(
                        f"{total_count} Ausgaben - {date_range[0].strftime('%d.%m.%Y')} bis {date_range[1].strftime('%d.%m.%Y')}"
                    )
            else:
                self.status_label.setText("Keine Ausgaben vorhanden - PDF laden oder manuell eingeben")
            
        except Exception as e:
            print(f"ERROR in refresh_expenses_dashboard: {e}")
            import traceback
            traceback.print_exc()
    
    def update_expenses_display(self):
        """Update chart and table for expenses."""
        try:
            if not hasattr(self, 'expenses_data_manager'):
                self.show_empty_expenses_state()
                return
            
            if self.expenses_data_manager.expenses_df.empty:
                self.show_empty_expenses_state()
                return
            
            # Get all expenses data
            data = self.expenses_data_manager.expenses_df.copy()
            
            if data is None or data.empty:
                self.show_empty_expenses_state()
                return
            
            # Aggregate monthly for chart
            data['YearMonth'] = data['Date'].dt.strftime('%Y-%m')
            monthly = data.groupby('YearMonth')['Amount'].sum().reset_index()
            monthly = monthly.sort_values('YearMonth')
            
            # Update chart
            if hasattr(self, 'chart'):
                self.chart.set_data(monthly, 'monthly', data)
            
            # Update table
            self.show_expenses_table(data)
            
        except Exception as e:
            print(f"ERROR in update_expenses_display: {e}")
            import traceback
            traceback.print_exc()
            self.show_empty_expenses_state()
    
    def show_empty_expenses_state(self):
        """Show empty state for expenses dashboard."""
        try:
            if hasattr(self, 'chart') and hasattr(self.chart, 'canvas'):
                self.chart.canvas.clear_chart()
                self.chart.canvas.ax.text(
                    0.5, 0.5, 
                    'Keine Ausgaben vorhanden\n\nKlicken Sie auf "PDF Laden" oder "Manuell eingeben"\num Ausgaben hinzuzufugen.',
                    ha='center', va='center',
                    fontsize=12, color=COLORS['text_muted'],
                    transform=self.chart.canvas.ax.transAxes
                )
                self.chart.canvas.draw()
            
            if hasattr(self, 'table'):
                self.table.setRowCount(0)
                self.table.setColumnCount(4)
                self.table.setHorizontalHeaderLabels(['Datum', 'Betrag', 'Beschreibung', 'Quelle'])
                
        except Exception as e:
            print(f"ERROR in show_empty_expenses_state: {e}")
    
    def show_expenses_table(self, data: pd.DataFrame):
        """Show expenses data in table (double-click to edit)."""
        try:
            self._current_table_view = 'all_data'
            self._table_expense_ids = []
            
            if data is None or data.empty:
                if hasattr(self, 'table'):
                    self.table.setRowCount(0)
                return
            
            # Sort by date descending
            data = data.sort_values('Date', ascending=False)
            
            if hasattr(self, 'table'):
                self.table.setColumnCount(5)
                self.table.setHorizontalHeaderLabels(['Datum', 'Betrag', 'Beschreibung', 'Kategorie', 'Quelle'])
                self.table.setRowCount(len(data))
                
                for i, (_, row) in enumerate(data.iterrows()):
                    self.table.setItem(i, 0, QTableWidgetItem(row['Date'].strftime('%d.%m.%Y')))
                    self.table.setItem(i, 1, QTableWidgetItem(f"EUR {row['Amount']:,.2f}".replace(',', '.')))
                    self.table.setItem(i, 2, QTableWidgetItem(str(row.get('Description', ''))))
                    self.table.setItem(i, 3, QTableWidgetItem(str(row.get('Category', 'Manuell'))))
                    self.table.setItem(i, 4, QTableWidgetItem(str(row.get('Source', ''))))
                    self._table_expense_ids.append(row.get('ID'))
                
                self.table.resizeColumnsToContents()
                
        except Exception as e:
            print(f"ERROR in show_expenses_table: {e}")
            import traceback
            traceback.print_exc()
    
    def update_expenses_analytics(self):
        """Update analytics panel for expenses data."""
        try:
            # Check if analytics panel exists
            if not hasattr(self, 'analytics_panel'):
                print("WARNING: analytics_panel not found")
                return
            
            # Check if data manager exists
            if not hasattr(self, 'expenses_data_manager'):
                self.analytics_panel.update_forecast({})
                return
            
            # Get filtered data
            if self.current_start_date and self.current_end_date:
                data = self.expenses_data_manager.filter_by_date_range(
                    self.current_start_date, self.current_end_date
                )
            else:
                data = self.expenses_data_manager.expenses_df
            
            if data is None or data.empty:
                self.analytics_panel.update_forecast({})
                if hasattr(self.analytics_panel, 'update_recommendations'):
                    self.analytics_panel.update_recommendations([])
                return
            
            # Get current method from combo
            if hasattr(self.analytics_panel, 'method_combo'):
                method = self.analytics_panel.method_combo.currentText()
            else:
                method = "Jahrestrend"
            
            method_map = {
                "Jahrestrend": "yearly_trend",
                "Kombiniert": "combined",
                "Monte Carlo": "monte_carlo",
                "Ensemble": "ensemble",
                "Linear": "linear",
                "Exponentiell": "exponential",
                "Gleitend": "moving_average",
                "Wachstum": "growth_rate"
            }
            method = method_map.get(method, "yearly_trend")
            
            forecast_engine = ForecastEngine(data)
            forecast = forecast_engine.forecast_with_horizons(method=method)
            self.analytics_panel.update_forecast(forecast)
            
        except Exception as e:
            print(f"Expenses forecast error: {e}")
            import traceback
            traceback.print_exc()
            if hasattr(self, 'analytics_panel'):
                self.analytics_panel.update_forecast({
                    'method': 'Fehler',
                    'interpretation': {'message': str(e)}
                })
    
    def show_cross_dashboard(self):
        """Show cross-dashboard analysis."""
        # Placeholder - will be implemented
        self.status_label.setText("🔄 Cross-Dashboard - Wird implementiert...")
        self.status_label.setStyleSheet(f"color: {COLORS['chart_yellow']};")
        
        self.chart.canvas.clear_chart()
        self.chart.canvas.ax.text(
            0.5, 0.5, 
            '🔄 Cross-Dashboard Analyse\n\nProfit = Einnahmen - Ausgaben\n\nKommt nach Marketing & Ausgaben...',
            ha='center', va='center',
            fontsize=14, color=COLORS['text_muted'],
            transform=self.chart.canvas.ax.transAxes
        )
        self.chart.canvas.draw()
        
        self.table.setRowCount(0)
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(['Cross-Dashboard'])


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

