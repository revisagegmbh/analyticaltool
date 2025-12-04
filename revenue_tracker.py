import sys
import re
from datetime import datetime
from pathlib import Path
import pdfplumber
import pandas as pd
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QFileDialog, QLabel, QHBoxLayout, QComboBox, QMessageBox)
from PyQt6.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class ExpenseTrackerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Expense Tracker")
        self.setGeometry(100, 100, 1200, 800)
        
        # Data storage
        self.expenses_df = pd.DataFrame(columns=['Date', 'Amount', 'Description', 'Source'])
        
        # Setup UI
        self.init_ui()
        
    def init_ui(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Top buttons
        button_layout = QHBoxLayout()
        self.load_btn = QPushButton("Load PDF Files")
        self.load_btn.clicked.connect(self.load_pdfs)
        button_layout.addWidget(self.load_btn)
        
        self.clear_btn = QPushButton("Clear Data")
        self.clear_btn.clicked.connect(self.clear_data)
        button_layout.addWidget(self.clear_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("No PDFs loaded. Click 'Load PDF Files' to begin.")
        layout.addWidget(self.status_label)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("View:"))
        
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Monthly Totals", "Yearly Totals", "All Data"])
        self.view_combo.currentTextChanged.connect(self.update_display)
        filter_layout.addWidget(self.view_combo)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Table for displaying data
        self.table = QTableWidget()
        layout.addWidget(self.table)
        
        # Graph
        self.figure = Figure(figsize=(10, 4))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
    def load_pdfs(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "Select PDF Files", 
            "", 
            "PDF Files (*.pdf)"
        )
        
        if not files:
            return
        
        new_expenses = []
        
        for file_path in files:
            try:
                expenses = self.parse_pdf(file_path)
                new_expenses.extend(expenses)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error parsing {Path(file_path).name}: {str(e)}")
        
        if new_expenses:
            new_df = pd.DataFrame(new_expenses)
            self.expenses_df = pd.concat([self.expenses_df, new_df], ignore_index=True)
            self.expenses_df['Date'] = pd.to_datetime(self.expenses_df['Date'])
            self.expenses_df = self.expenses_df.sort_values('Date')
            
            self.status_label.setText(f"Loaded {len(new_expenses)} expenses from {len(files)} PDF(s)")
            self.update_display()
        else:
            self.status_label.setText("No expenses found in the selected PDFs")
    
    def parse_pdf(self, file_path):
        """
        Parse Revisage invoice PDFs and extract net amount and date.
        Looks for "Zwischensumme" (subtotal/net amount) and invoice date.
        """
        expenses = []
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                
                if not text:
                    continue
                
                # Extract invoice date (format: DD.MM.YYYY)
                # Look for "Datum" field followed by the date
                date_match = re.search(r'Datum\s+(\d{2}\.\d{2}\.\d{4})', text)
                invoice_date = None
                
                if date_match:
                    try:
                        invoice_date = datetime.strptime(date_match.group(1), '%d.%m.%Y')
                    except ValueError:
                        pass
                
                # If no date found with "Datum", try to find any date in DD.MM.YYYY format
                if not invoice_date:
                    date_match = re.search(r'\b(\d{2}\.\d{2}\.\d{4})\b', text)
                    if date_match:
                        try:
                            invoice_date = datetime.strptime(date_match.group(1), '%d.%m.%Y')
                        except ValueError:
                            invoice_date = datetime.now()
                    else:
                        invoice_date = datetime.now()
                
                # Extract net amount (Zwischensumme)
                # Pattern: "Zwischensumme" followed by amount (format: 138,60 or 138.60)
                net_amount = None
                
                # Try to find "Zwischensumme" line with EUR amount
                zwischensumme_match = re.search(r'Zwischensumme\s+(?:EUR\s+)?(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})', text)
                
                if zwischensumme_match:
                    amount_str = zwischensumme_match.group(1)
                    # Convert European format (123.456,78) to float
                    amount_str = amount_str.replace('.', '').replace(',', '.')
                    try:
                        net_amount = float(amount_str)
                    except ValueError:
                        pass
                
                # If Zwischensumme not found, look for invoices without tax
                # These might have "Endsumme" as the net amount
                if not net_amount:
                    # Check if there's no tax line (invoices with UID)
                    if 'incl. MwSt.' not in text and 'Steuercode' not in text:
                        endsumme_match = re.search(r'Endsumme\s+(?:EUR\s+)?(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})', text)
                        if endsumme_match:
                            amount_str = endsumme_match.group(1)
                            amount_str = amount_str.replace('.', '').replace(',', '.')
                            try:
                                net_amount = float(amount_str)
                            except ValueError:
                                pass
                
                # Extract invoice number for description
                invoice_number = "Unknown"
                invoice_match = re.search(r'Belegnummer\s+(\d+-\d+)', text)
                if invoice_match:
                    invoice_number = invoice_match.group(1)
                
                # Add expense if we found both date and amount
                if invoice_date and net_amount:
                    expenses.append({
                        'Date': invoice_date,
                        'Amount': net_amount,
                        'Description': f'Invoice {invoice_number}',
                        'Source': Path(file_path).name
                    })
        
        return expenses
    
    def update_display(self):
        if self.expenses_df.empty:
            return
        
        view_type = self.view_combo.currentText()
        
        if view_type == "Monthly Totals":
            self.show_monthly_view()
        elif view_type == "Yearly Totals":
            self.show_yearly_view()
        else:
            self.show_all_data()
        
        self.update_graph()
    
    def show_monthly_view(self):
        # Group by year-month
        monthly = self.expenses_df.copy()
        monthly['YearMonth'] = monthly['Date'].dt.to_period('M')
        grouped = monthly.groupby('YearMonth')['Amount'].sum().reset_index()
        grouped['YearMonth'] = grouped['YearMonth'].astype(str)
        
        # Update table
        self.table.setRowCount(len(grouped))
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['Month', 'Total Amount'])
        
        for i, row in grouped.iterrows():
            self.table.setItem(i, 0, QTableWidgetItem(row['YearMonth']))
            self.table.setItem(i, 1, QTableWidgetItem(f"${row['Amount']:.2f}"))
        
        self.table.resizeColumnsToContents()
    
    def show_yearly_view(self):
        # Group by year
        yearly = self.expenses_df.copy()
        yearly['Year'] = yearly['Date'].dt.year
        grouped = yearly.groupby('Year')['Amount'].sum().reset_index()
        
        # Update table
        self.table.setRowCount(len(grouped))
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['Year', 'Total Amount'])
        
        for i, row in grouped.iterrows():
            self.table.setItem(i, 0, QTableWidgetItem(str(row['Year'])))
            self.table.setItem(i, 1, QTableWidgetItem(f"${row['Amount']:.2f}"))
        
        self.table.resizeColumnsToContents()
    
    def show_all_data(self):
        # Show all expenses
        self.table.setRowCount(len(self.expenses_df))
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Date', 'Amount', 'Description', 'Source'])
        
        for i, row in self.expenses_df.iterrows():
            self.table.setItem(i, 0, QTableWidgetItem(row['Date'].strftime('%Y-%m-%d')))
            self.table.setItem(i, 1, QTableWidgetItem(f"${row['Amount']:.2f}"))
            self.table.setItem(i, 2, QTableWidgetItem(row['Description']))
            self.table.setItem(i, 3, QTableWidgetItem(row['Source']))
        
        self.table.resizeColumnsToContents()
    
    def update_graph(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        view_type = self.view_combo.currentText()
        
        if view_type == "Monthly Totals":
            monthly = self.expenses_df.copy()
            monthly['YearMonth'] = monthly['Date'].dt.to_period('M')
            grouped = monthly.groupby('YearMonth')['Amount'].sum()
            
            ax.bar(range(len(grouped)), grouped.values)
            ax.set_xticks(range(len(grouped)))
            ax.set_xticklabels([str(x) for x in grouped.index], rotation=45, ha='right')
            ax.set_ylabel('Amount ($)')
            ax.set_title('Monthly Expenses')
            
        elif view_type == "Yearly Totals":
            yearly = self.expenses_df.copy()
            yearly['Year'] = yearly['Date'].dt.year
            grouped = yearly.groupby('Year')['Amount'].sum()
            
            ax.bar(grouped.index, grouped.values)
            ax.set_xlabel('Year')
            ax.set_ylabel('Amount ($)')
            ax.set_title('Yearly Expenses')
        
        else:
            # Scatter plot of all expenses
            ax.scatter(self.expenses_df['Date'], self.expenses_df['Amount'])
            ax.set_xlabel('Date')
            ax.set_ylabel('Amount ($)')
            ax.set_title('All Expenses')
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def clear_data(self):
        self.expenses_df = pd.DataFrame(columns=['Date', 'Amount', 'Description', 'Source'])
        self.table.setRowCount(0)
        self.figure.clear()
        self.canvas.draw()
        self.status_label.setText("Data cleared. Load PDFs to begin.")


def main():
    app = QApplication(sys.argv)
    window = ExpenseTrackerApp()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
