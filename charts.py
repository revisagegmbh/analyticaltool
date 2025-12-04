"""
Charts Module - Advanced Visualizations (Phase 2)
Features: Multiple chart types, Drill-down, Interactive tooltips, Heatmaps
"""

from typing import Optional, List, Tuple, Dict, Any, Callable
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.patches import Wedge
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, 
    QCheckBox, QPushButton, QStackedWidget, QFrame, QToolTip
)
from PyQt6.QtCore import pyqtSignal, Qt, QPoint
from PyQt6.QtGui import QCursor

from styles import COLORS, CHART_COLORS, apply_matplotlib_style


class ChartCanvas(FigureCanvas):
    """Matplotlib canvas for embedding in PyQt6 with interactive features."""
    
    # Signal for click events (for drill-down)
    bar_clicked = pyqtSignal(object)  # Emits clicked data
    
    def __init__(self, parent=None, width=10, height=6, dpi=100):
        apply_matplotlib_style()
        
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig.patch.set_facecolor(COLORS['bg_medium'])
        
        super().__init__(self.fig)
        self.setParent(parent)
        
        self.ax = self.fig.add_subplot(111)
        self._apply_axes_style()
        
        # Interactive elements
        self._click_data = {}  # Store data for click events
        self._tooltip_annotation = None
        
        # Connect mouse events
        self.mpl_connect('button_press_event', self._on_click)
        self.mpl_connect('motion_notify_event', self._on_hover)
    
    def _apply_axes_style(self):
        """Apply dark theme styling to axes."""
        self.ax.set_facecolor(COLORS['bg_medium'])
        self.ax.tick_params(colors=COLORS['text_secondary'])
        self.ax.xaxis.label.set_color(COLORS['text_primary'])
        self.ax.yaxis.label.set_color(COLORS['text_primary'])
        self.ax.title.set_color(COLORS['text_primary'])
        
        for spine in self.ax.spines.values():
            spine.set_color(COLORS['border'])
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        
        self.ax.grid(True, linestyle='--', alpha=0.3, color=COLORS['border'])
        self.ax.set_axisbelow(True)
    
    def clear_chart(self):
        """Clear the current chart."""
        self.fig.clear()
        self.ax = self.fig.add_subplot(111)
        self._apply_axes_style()
        self._click_data = {}
    
    def set_click_data(self, data: Dict[int, Any]):
        """Set data mapping for click events (bar index -> data)."""
        self._click_data = data
    
    def _on_click(self, event):
        """Handle mouse click events for drill-down."""
        if event.inaxes != self.ax:
            return
        
        # Check if clicking on a bar
        for i, (idx, data) in enumerate(self._click_data.items()):
            bars = [child for child in self.ax.get_children() 
                   if hasattr(child, 'get_x') and hasattr(child, 'get_width')]
            
            for bar in bars:
                if bar.contains(event)[0]:
                    # Find which bar was clicked
                    bar_x = bar.get_x()
                    bar_idx = int(round(bar_x + bar.get_width() / 2))
                    if bar_idx in self._click_data:
                        self.bar_clicked.emit(self._click_data[bar_idx])
                    return
    
    def _on_hover(self, event):
        """Handle mouse hover for interactive tooltips."""
        if event.inaxes != self.ax:
            if self._tooltip_annotation:
                self._tooltip_annotation.set_visible(False)
                self.draw_idle()
            return
        
        # Check bars for hover
        for child in self.ax.get_children():
            if hasattr(child, 'get_x') and hasattr(child, 'get_width') and hasattr(child, 'get_height'):
                if child.contains(event)[0]:
                    height = child.get_height()
                    x = child.get_x() + child.get_width() / 2
                    
                    # Create or update tooltip
                    if self._tooltip_annotation is None:
                        self._tooltip_annotation = self.ax.annotate(
                            f'€{height:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
                            xy=(x, height),
                            xytext=(0, 15),
                            textcoords='offset points',
                            ha='center',
                            va='bottom',
                            fontsize=11,
                            fontweight='bold',
                            color='white',
                            bbox=dict(
                                boxstyle='round,pad=0.5',
                                facecolor=COLORS['primary'],
                                edgecolor='none',
                                alpha=0.9
                            )
                        )
                    else:
                        self._tooltip_annotation.xy = (x, height)
                        self._tooltip_annotation.set_text(
                            f'€{height:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
                        )
                        self._tooltip_annotation.set_visible(True)
                    
                    self.draw_idle()
                    return
        
        # Hide tooltip if not hovering over anything
        if self._tooltip_annotation:
            self._tooltip_annotation.set_visible(False)
            self.draw_idle()


class ExpenseChart(QWidget):
    """Main chart widget with multiple visualization options (Phase 2)."""
    
    # Signal for drill-down navigation
    drill_down_requested = pyqtSignal(str, object)  # (level, data)
    
    CHART_TYPES = [
        "Balkendiagramm",
        "Liniendiagramm", 
        "Kreisdiagramm",
        "Donut-Diagramm",
        "Heatmap",
        "Gestapeltes Balkendiagramm",
        "Periodenvergleich"
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        self.raw_data = None  # Full dataset for drill-down
        self.show_trend = True
        self.trend_window = 3
        self.current_drill_level = 'overview'  # 'overview', 'year', 'month'
        self.drill_context = {}  # Store context for drill navigation
        self.comparison_data = None  # For period comparison
        self.init_ui()
    
    def init_ui(self):
        """Initialize the chart widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Chart controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(16)
        
        # Chart type selector
        chart_label = QLabel("Diagrammtyp:")
        chart_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 600;")
        controls_layout.addWidget(chart_label)
        
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(self.CHART_TYPES)
        self.chart_type_combo.currentTextChanged.connect(self.on_chart_type_changed)
        self.chart_type_combo.setMinimumWidth(180)
        controls_layout.addWidget(self.chart_type_combo)
        
        # Trend line toggle
        self.trend_checkbox = QCheckBox("Trendlinie")
        self.trend_checkbox.setChecked(True)
        self.trend_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS['text_secondary']};
                spacing: 8px;
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
        """)
        self.trend_checkbox.stateChanged.connect(self.on_trend_toggle)
        controls_layout.addWidget(self.trend_checkbox)
        
        # Drill-down navigation
        self.breadcrumb_frame = QFrame()
        self.breadcrumb_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border-radius: 6px;
                padding: 4px 8px;
            }}
        """)
        breadcrumb_layout = QHBoxLayout(self.breadcrumb_frame)
        breadcrumb_layout.setContentsMargins(8, 4, 8, 4)
        breadcrumb_layout.setSpacing(4)
        
        self.back_btn = QPushButton("← Zurück")
        self.back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['primary']};
                border: none;
                padding: 4px 8px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                color: {COLORS['primary_light']};
            }}
        """)
        self.back_btn.clicked.connect(self.navigate_back)
        self.back_btn.setVisible(False)
        breadcrumb_layout.addWidget(self.back_btn)
        
        self.breadcrumb_label = QLabel("Übersicht")
        self.breadcrumb_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 500;")
        breadcrumb_layout.addWidget(self.breadcrumb_label)
        
        breadcrumb_layout.addStretch()
        controls_layout.addWidget(self.breadcrumb_frame)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Tooltip hint
        hint_label = QLabel("💡 Tipp: Klicken Sie auf Balken für Details")
        hint_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        layout.addWidget(hint_label)
        
        # Chart canvas
        self.canvas = ChartCanvas(self, width=12, height=5)
        self.canvas.bar_clicked.connect(self.on_bar_clicked)
        layout.addWidget(self.canvas)
    
    def on_chart_type_changed(self, chart_type: str):
        """Handle chart type changes."""
        # Show/hide trend checkbox based on chart type
        show_trend_option = chart_type in ["Balkendiagramm", "Liniendiagramm"]
        self.trend_checkbox.setVisible(show_trend_option)
        self.refresh_chart()
    
    def on_trend_toggle(self, state):
        """Handle trend line checkbox toggle."""
        self.show_trend = bool(state)
        self.refresh_chart()
    
    def set_data(self, df: pd.DataFrame, view_type: str, raw_data: pd.DataFrame = None):
        """Set data for the chart.
        
        Args:
            df: Aggregated DataFrame for display.
            view_type: Type of view ('monthly', 'yearly', 'all', 'comparison').
            raw_data: Full DataFrame for drill-down capabilities.
        """
        self.data = df
        self.view_type = view_type
        if raw_data is not None:
            self.raw_data = raw_data
        self.refresh_chart()
    
    def set_comparison_data(self, period1_data: pd.DataFrame, period2_data: pd.DataFrame,
                           period1_label: str, period2_label: str):
        """Set data for period comparison chart."""
        self.comparison_data = {
            'period1': period1_data,
            'period2': period2_data,
            'label1': period1_label,
            'label2': period2_label
        }
        if self.chart_type_combo.currentText() == "Periodenvergleich":
            self.refresh_chart()
    
    def refresh_chart(self):
        """Refresh the chart with current data and settings."""
        if self.data is None or self.data.empty:
            self._draw_empty_state()
            return
        
        chart_type = self.chart_type_combo.currentText()
        
        if chart_type == "Balkendiagramm":
            self._draw_bar_chart()
        elif chart_type == "Liniendiagramm":
            self._draw_line_chart()
        elif chart_type == "Kreisdiagramm":
            self._draw_pie_chart()
        elif chart_type == "Donut-Diagramm":
            self._draw_donut_chart()
        elif chart_type == "Heatmap":
            self._draw_heatmap()
        elif chart_type == "Gestapeltes Balkendiagramm":
            self._draw_stacked_bar_chart()
        elif chart_type == "Periodenvergleich":
            self._draw_comparison_chart()
        
        self.canvas.fig.tight_layout()
        self.canvas.draw()
    
    def _draw_empty_state(self):
        """Draw empty state message."""
        self.canvas.clear_chart()
        self.canvas.ax.text(
            0.5, 0.5, 'Keine Daten verfügbar\n\nLaden Sie PDF-Rechnungen um zu beginnen',
            ha='center', va='center',
            fontsize=14, color=COLORS['text_muted'],
            transform=self.canvas.ax.transAxes
        )
        self.canvas.draw()
    
    def _draw_bar_chart(self):
        """Draw a bar chart with drill-down capability."""
        self.canvas.clear_chart()
        ax = self.canvas.ax
        
        if self.view_type == 'monthly':
            x_data = self.data['YearMonth'].tolist()
            y_data = self.data['Amount'].tolist()
            title = 'Monatliche Einnahmen'
        elif self.view_type == 'yearly':
            x_data = [str(int(y)) for y in self.data['Year'].tolist()]
            y_data = self.data['Amount'].tolist()
            title = 'Jährliche Einnahmen'
        else:
            x_data = range(len(self.data))
            y_data = self.data['Amount'].tolist()
            title = 'Einnahmen'
        
        # Create bars
        bars = ax.bar(
            range(len(y_data)), y_data,
            color=COLORS['chart_blue'],
            edgecolor='none',
            alpha=0.9,
            width=0.7
        )
        
        # Store click data for drill-down
        click_data = {}
        for i, (x_val, y_val) in enumerate(zip(x_data, y_data)):
            click_data[i] = {'label': x_val, 'value': y_val, 'type': self.view_type}
        self.canvas.set_click_data(click_data)
        
        # Value labels
        for bar, value in zip(bars, y_data):
            height = bar.get_height()
            ax.annotate(
                f'€{value:,.0f}'.replace(',', '.'),
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 5),
                textcoords="offset points",
                ha='center', va='bottom',
                fontsize=9,
                color=COLORS['text_secondary'],
                fontweight='bold'
            )
        
        # Trend line
        if self.show_trend and len(y_data) >= self.trend_window:
            self._add_trend_line(ax, y_data)
        
        ax.set_xticks(range(len(x_data)))
        ax.set_xticklabels(x_data, rotation=45, ha='right', fontsize=10)
        ax.set_ylabel('Betrag (€)', fontsize=11, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.yaxis.set_major_formatter(lambda x, p: f'€{x:,.0f}'.replace(',', '.'))
    
    def _draw_line_chart(self):
        """Draw a line chart."""
        self.canvas.clear_chart()
        ax = self.canvas.ax
        
        if self.view_type == 'monthly':
            x_data = self.data['YearMonth'].tolist()
            y_data = self.data['Amount'].tolist()
            title = 'Monatliche Einnahmen - Trend'
        elif self.view_type == 'yearly':
            x_data = [str(int(y)) for y in self.data['Year'].tolist()]
            y_data = self.data['Amount'].tolist()
            title = 'Jährliche Einnahmen - Trend'
        else:
            x_data = range(len(self.data))
            y_data = self.data['Amount'].tolist()
            title = 'Einnahmen - Trend'
        
        # Main line with markers
        ax.plot(
            range(len(y_data)), y_data,
            color=COLORS['chart_blue'],
            linewidth=3,
            marker='o',
            markersize=10,
            markerfacecolor=COLORS['chart_cyan'],
            markeredgecolor=COLORS['chart_blue'],
            markeredgewidth=2,
            label='Einnahmen'
        )
        
        # Fill under line
        ax.fill_between(range(len(y_data)), y_data, alpha=0.15, color=COLORS['chart_blue'])
        
        # Trend line
        if self.show_trend and len(y_data) >= self.trend_window:
            self._add_trend_line(ax, y_data, style='projection')
        
        # Data labels
        for i, value in enumerate(y_data):
            ax.annotate(
                f'€{value:,.0f}'.replace(',', '.'),
                xy=(i, value),
                xytext=(0, 12),
                textcoords="offset points",
                ha='center', va='bottom',
                fontsize=9,
                color=COLORS['text_secondary'],
                fontweight='bold'
            )
        
        ax.set_xticks(range(len(x_data)))
        ax.set_xticklabels(x_data, rotation=45, ha='right', fontsize=10)
        ax.set_ylabel('Betrag (€)', fontsize=11, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.legend(loc='upper left', framealpha=0.9)
        ax.yaxis.set_major_formatter(lambda x, p: f'€{x:,.0f}'.replace(',', '.'))
    
    def _draw_pie_chart(self):
        """Draw a pie chart for category or period distribution."""
        self.canvas.clear_chart()
        ax = self.canvas.ax
        
        # Remove axis styling for pie chart
        ax.set_facecolor(COLORS['bg_medium'])
        ax.axis('equal')
        
        if self.view_type == 'monthly':
            labels = self.data['YearMonth'].tolist()
            values = self.data['Amount'].tolist()
            title = 'Einnahmenverteilung nach Monat'
        elif self.view_type == 'yearly':
            labels = [str(int(y)) for y in self.data['Year'].tolist()]
            values = self.data['Amount'].tolist()
            title = 'Einnahmenverteilung nach Jahr'
        else:
            # Group by category if available
            if 'Category' in self.data.columns:
                grouped = self.data.groupby('Category')['Amount'].sum()
                labels = grouped.index.tolist()
                values = grouped.values.tolist()
                title = 'Einnahmenverteilung nach Kategorie'
            else:
                labels = ['Gesamt']
                values = [self.data['Amount'].sum()]
                title = 'Einnahmenverteilung'
        
        # Limit to top 8 categories + "Sonstige"
        if len(labels) > 8:
            sorted_idx = np.argsort(values)[::-1]
            top_labels = [labels[i] for i in sorted_idx[:7]]
            top_values = [values[i] for i in sorted_idx[:7]]
            other_value = sum([values[i] for i in sorted_idx[7:]])
            labels = top_labels + ['Sonstige']
            values = top_values + [other_value]
        
        # Colors
        colors = CHART_COLORS[:len(labels)]
        
        # Create pie
        wedges, texts, autotexts = ax.pie(
            values,
            labels=None,
            autopct=lambda pct: f'{pct:.1f}%' if pct > 5 else '',
            colors=colors,
            startangle=90,
            explode=[0.02] * len(values),
            shadow=False,
            textprops={'color': 'white', 'fontweight': 'bold', 'fontsize': 10}
        )
        
        # Legend
        legend_labels = [f'{l}: €{v:,.0f}'.replace(',', '.') for l, v in zip(labels, values)]
        ax.legend(
            wedges, legend_labels,
            loc='center left',
            bbox_to_anchor=(1, 0.5),
            fontsize=10,
            framealpha=0.9
        )
        
        ax.set_title(title, fontsize=14, fontweight='bold', color=COLORS['text_primary'], pad=20)
    
    def _draw_donut_chart(self):
        """Draw a donut chart with center text."""
        self.canvas.clear_chart()
        ax = self.canvas.ax
        
        ax.set_facecolor(COLORS['bg_medium'])
        ax.axis('equal')
        
        if self.view_type == 'monthly':
            labels = self.data['YearMonth'].tolist()[-6:]  # Last 6 months
            values = self.data['Amount'].tolist()[-6:]
            title = 'Letzte 6 Monate'
        elif self.view_type == 'yearly':
            labels = [str(int(y)) for y in self.data['Year'].tolist()]
            values = self.data['Amount'].tolist()
            title = 'Jahresverteilung'
        else:
            labels = self.data['YearMonth'].tolist() if 'YearMonth' in self.data.columns else ['Gesamt']
            values = self.data['Amount'].tolist() if len(self.data) > 1 else [self.data['Amount'].sum()]
            title = 'Einnahmenverteilung'
        
        colors = CHART_COLORS[:len(labels)]
        total = sum(values)
        
        # Create donut
        wedges, texts, autotexts = ax.pie(
            values,
            labels=None,
            autopct=lambda pct: f'{pct:.0f}%' if pct > 8 else '',
            colors=colors,
            startangle=90,
            wedgeprops=dict(width=0.5, edgecolor=COLORS['bg_medium']),
            textprops={'color': 'white', 'fontweight': 'bold', 'fontsize': 11}
        )
        
        # Center text
        ax.text(0, 0, f'€{total:,.0f}'.replace(',', '.'), 
                ha='center', va='center',
                fontsize=20, fontweight='bold', 
                color=COLORS['text_primary'])
        ax.text(0, -0.15, 'Gesamt', 
                ha='center', va='center',
                fontsize=11, color=COLORS['text_secondary'])
        
        # Legend
        legend_labels = [f'{l}: €{v:,.0f}'.replace(',', '.') for l, v in zip(labels, values)]
        ax.legend(
            wedges, legend_labels,
            loc='center left',
            bbox_to_anchor=(1, 0.5),
            fontsize=9,
            framealpha=0.9
        )
        
        ax.set_title(title, fontsize=14, fontweight='bold', color=COLORS['text_primary'], pad=20)
    
    def _draw_heatmap(self):
        """Draw a heatmap showing expenses by month/year grid."""
        self.canvas.clear_chart()
        ax = self.canvas.ax
        
        if self.raw_data is None or self.raw_data.empty:
            self._draw_empty_state()
            return
        
        # Create pivot table: rows=months, columns=years
        df = self.raw_data.copy()
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month
        
        pivot = df.pivot_table(
            values='Amount', 
            index='Month', 
            columns='Year', 
            aggfunc='sum',
            fill_value=0
        )
        
        # Month names (German)
        month_names = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
        
        # Ensure all months are present
        for m in range(1, 13):
            if m not in pivot.index:
                pivot.loc[m] = 0
        pivot = pivot.sort_index()
        
        # Create heatmap
        im = ax.imshow(
            pivot.values, 
            cmap='YlOrRd',
            aspect='auto'
        )
        
        # Labels
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns.astype(int), fontsize=10)
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels([month_names[m-1] for m in pivot.index], fontsize=10)
        
        # Add value annotations
        for i in range(len(pivot.index)):
            for j in range(len(pivot.columns)):
                value = pivot.values[i, j]
                if value > 0:
                    text_color = 'white' if value > pivot.values.max() * 0.5 else COLORS['text_primary']
                    ax.text(j, i, f'€{value:,.0f}'.replace(',', '.'),
                           ha='center', va='center', fontsize=8,
                           color=text_color, fontweight='bold')
        
        # Colorbar
        cbar = self.canvas.fig.colorbar(im, ax=ax, shrink=0.8)
        cbar.ax.yaxis.set_major_formatter(lambda x, p: f'€{x:,.0f}'.replace(',', '.'))
        cbar.ax.tick_params(colors=COLORS['text_secondary'])
        
        ax.set_xlabel('Jahr', fontsize=11, fontweight='bold')
        ax.set_ylabel('Monat', fontsize=11, fontweight='bold')
        ax.set_title('Einnahmen-Heatmap (Monat × Jahr)', fontsize=14, fontweight='bold', pad=15)
        
        # Remove grid for heatmap
        ax.grid(False)
    
    def _draw_stacked_bar_chart(self):
        """Draw a stacked bar chart comparing categories over time."""
        self.canvas.clear_chart()
        ax = self.canvas.ax
        
        if self.raw_data is None or self.raw_data.empty:
            self._draw_empty_state()
            return
        
        df = self.raw_data.copy()
        
        # Group by period and category
        if self.view_type == 'yearly':
            df['Period'] = df['Date'].dt.year
        else:
            df['Period'] = df['Date'].dt.to_period('M').astype(str)
        
        # Create pivot for stacking
        if 'Category' in df.columns and df['Category'].nunique() > 1:
            pivot = df.pivot_table(
                values='Amount',
                index='Period',
                columns='Category',
                aggfunc='sum',
                fill_value=0
            )
        else:
            # If no categories, create dummy categories by quarter
            df['Quarter'] = 'Q' + df['Date'].dt.quarter.astype(str)
            pivot = df.pivot_table(
                values='Amount',
                index='Period',
                columns='Quarter',
                aggfunc='sum',
                fill_value=0
            )
        
        # Plot stacked bars
        x = range(len(pivot.index))
        bottom = np.zeros(len(pivot.index))
        
        for i, col in enumerate(pivot.columns):
            color = CHART_COLORS[i % len(CHART_COLORS)]
            ax.bar(x, pivot[col].values, bottom=bottom, label=col, 
                  color=color, width=0.7, alpha=0.9)
            bottom += pivot[col].values
        
        ax.set_xticks(x)
        ax.set_xticklabels(pivot.index, rotation=45, ha='right', fontsize=10)
        ax.set_ylabel('Betrag (€)', fontsize=11, fontweight='bold')
        ax.set_title('Gestapelte Einnahmen', fontsize=14, fontweight='bold', pad=15)
        ax.legend(loc='upper left', fontsize=9, framealpha=0.9)
        ax.yaxis.set_major_formatter(lambda x, p: f'€{x:,.0f}'.replace(',', '.'))
    
    def _draw_comparison_chart(self):
        """Draw dual-axis comparison chart for two periods."""
        self.canvas.clear_chart()
        ax = self.canvas.ax
        
        if self.comparison_data is None:
            # If no comparison data, compare last two years
            if self.raw_data is None or self.raw_data.empty:
                self._draw_empty_state()
                return
            
            df = self.raw_data.copy()
            df['Year'] = df['Date'].dt.year
            years = sorted(df['Year'].unique())
            
            if len(years) < 2:
                ax.text(0.5, 0.5, 'Mindestens 2 Jahre Daten erforderlich\nfür Periodenvergleich',
                       ha='center', va='center', fontsize=12, color=COLORS['text_muted'],
                       transform=ax.transAxes)
                self.canvas.draw()
                return
            
            # Compare last two years
            year1, year2 = years[-2], years[-1]
            
            df1 = df[df['Year'] == year1].copy()
            df2 = df[df['Year'] == year2].copy()
            
            df1['Month'] = df1['Date'].dt.month
            df2['Month'] = df2['Date'].dt.month
            
            monthly1 = df1.groupby('Month')['Amount'].sum()
            monthly2 = df2.groupby('Month')['Amount'].sum()
            
            label1, label2 = str(year1), str(year2)
        else:
            monthly1 = self.comparison_data['period1']
            monthly2 = self.comparison_data['period2']
            label1 = self.comparison_data['label1']
            label2 = self.comparison_data['label2']
        
        # Month names
        month_names = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
        
        x = np.arange(12)
        width = 0.35
        
        # Ensure all months present
        values1 = [monthly1.get(m, 0) for m in range(1, 13)]
        values2 = [monthly2.get(m, 0) for m in range(1, 13)]
        
        # Create grouped bars
        bars1 = ax.bar(x - width/2, values1, width, label=label1, 
                      color=COLORS['chart_blue'], alpha=0.9)
        bars2 = ax.bar(x + width/2, values2, width, label=label2,
                      color=COLORS['chart_orange'], alpha=0.9)
        
        ax.set_xticks(x)
        ax.set_xticklabels(month_names, fontsize=10)
        ax.set_ylabel('Betrag (€)', fontsize=11, fontweight='bold')
        ax.set_title(f'Periodenvergleich: {label1} vs {label2}', 
                    fontsize=14, fontweight='bold', pad=15)
        ax.legend(loc='upper right', fontsize=10, framealpha=0.9)
        ax.yaxis.set_major_formatter(lambda x, p: f'€{x:,.0f}'.replace(',', '.'))
        
        # Add percentage change labels
        for i, (v1, v2) in enumerate(zip(values1, values2)):
            if v1 > 0 and v2 > 0:
                pct_change = ((v2 - v1) / v1) * 100
                color = COLORS['kpi_positive'] if pct_change > 0 else COLORS['kpi_negative']
                ax.annotate(
                    f'{pct_change:+.0f}%',
                    xy=(i, max(v1, v2)),
                    xytext=(0, 5),
                    textcoords='offset points',
                    ha='center', va='bottom',
                    fontsize=8, fontweight='bold',
                    color=color
                )
    
    def _add_trend_line(self, ax, y_data: List[float], style: str = 'moving_avg'):
        """Add a trend line to the chart."""
        x = np.arange(len(y_data))
        y = np.array(y_data)
        
        if style == 'moving_avg':
            window = min(self.trend_window, len(y_data))
            trend = pd.Series(y).rolling(window=window, center=True).mean()
            ax.plot(x, trend, color=COLORS['chart_orange'], linewidth=2.5,
                   linestyle='--', label=f'Ø {window}M', alpha=0.9)
        else:
            z = np.polyfit(x, y, 1)
            p = np.poly1d(z)
            x_ext = np.append(x, [len(y_data), len(y_data) + 1])
            ax.plot(x_ext, p(x_ext), color=COLORS['chart_orange'], linewidth=2,
                   linestyle='--', label='Trend', alpha=0.8)
        
        ax.legend(loc='upper left', framealpha=0.9)
    
    def draw_scatter(self, df: pd.DataFrame):
        """Draw a scatter plot for all expenses."""
        self.canvas.clear_chart()
        ax = self.canvas.ax
        
        if df.empty:
            self._draw_empty_state()
            return
        
        scatter = ax.scatter(
            df['Date'], df['Amount'],
            c=COLORS['chart_blue'],
            s=80, alpha=0.7,
            edgecolors=COLORS['chart_cyan'],
            linewidths=2
        )
        
        if self.show_trend and len(df) >= 3:
            x_numeric = (df['Date'] - df['Date'].min()).dt.days.values
            y = df['Amount'].values
            z = np.polyfit(x_numeric, y, 1)
            p = np.poly1d(z)
            ax.plot(df['Date'], p(x_numeric), color=COLORS['chart_orange'],
                   linewidth=2, linestyle='--', label='Trend', alpha=0.8)
            ax.legend(loc='upper left', framealpha=0.9)
        
        ax.set_xlabel('Datum', fontsize=11, fontweight='bold')
        ax.set_ylabel('Betrag (€)', fontsize=11, fontweight='bold')
        ax.set_title('Alle Einnahmen', fontsize=14, fontweight='bold', pad=15)
        
        for label in ax.get_xticklabels():
            label.set_rotation(45)
            label.set_ha('right')
        
        ax.yaxis.set_major_formatter(lambda x, p: f'€{x:,.0f}'.replace(',', '.'))
        self.canvas.fig.tight_layout()
        self.canvas.draw()
    
    # =========================================================================
    # Drill-Down Navigation
    # =========================================================================
    
    def on_bar_clicked(self, data: Dict):
        """Handle bar click for drill-down."""
        if data['type'] == 'yearly':
            # Drill down to monthly view for that year
            self.drill_context['year'] = data['label']
            self.current_drill_level = 'year'
            self.back_btn.setVisible(True)
            self.breadcrumb_label.setText(f"Übersicht → {data['label']}")
            self.drill_down_requested.emit('year', data['label'])
        
        elif data['type'] == 'monthly':
            # Drill down to individual invoices for that month
            self.drill_context['month'] = data['label']
            self.current_drill_level = 'month'
            self.back_btn.setVisible(True)
            year_ctx = self.drill_context.get('year', '')
            self.breadcrumb_label.setText(f"Übersicht → {year_ctx} → {data['label']}")
            self.drill_down_requested.emit('month', data['label'])
    
    def navigate_back(self):
        """Navigate back in drill-down hierarchy."""
        if self.current_drill_level == 'month':
            self.current_drill_level = 'year'
            year = self.drill_context.get('year', '')
            self.breadcrumb_label.setText(f"Übersicht → {year}")
            self.drill_down_requested.emit('back_to_year', year)
        
        elif self.current_drill_level == 'year':
            self.current_drill_level = 'overview'
            self.back_btn.setVisible(False)
            self.breadcrumb_label.setText("Übersicht")
            self.drill_context = {}
            self.drill_down_requested.emit('back_to_overview', None)
    
    def reset_drill_down(self):
        """Reset drill-down navigation to overview."""
        self.current_drill_level = 'overview'
        self.drill_context = {}
        self.back_btn.setVisible(False)
        self.breadcrumb_label.setText("Übersicht")
