"""
Styles Module - Corporate Blue Dark Theme
Designed for Desktop App compatibility with PyInstaller/cx_Freeze
"""

# Color Palette - Corporate Blue Dark Theme
COLORS = {
    # Primary colors
    'primary': '#1E88E5',           # Corporate Blue
    'primary_light': '#42A5F5',     # Lighter blue for hover
    'primary_dark': '#1565C0',      # Darker blue for pressed
    
    # Background colors (Dark Theme)
    'bg_dark': '#0D1117',           # Main background
    'bg_medium': '#161B22',         # Card background
    'bg_light': '#21262D',          # Lighter elements
    'bg_elevated': '#30363D',       # Elevated surfaces
    
    # Text colors
    'text_primary': '#E6EDF3',      # Main text
    'text_secondary': '#8B949E',    # Secondary text
    'text_muted': '#6E7681',        # Muted text
    
    # Accent colors for charts (bright & contrasting)
    'chart_blue': '#58A6FF',        # Bright blue
    'chart_green': '#3FB950',       # Success green
    'chart_red': '#F85149',         # Alert red
    'chart_orange': '#F0883E',      # Warning orange
    'chart_purple': '#A371F7',      # Purple accent
    'chart_cyan': '#39D5FF',        # Cyan accent
    'chart_yellow': '#F9E24E',      # Yellow accent
    'chart_pink': '#FF7EB6',        # Pink accent
    
    # Status colors
    'success': '#238636',
    'warning': '#9E6A03',
    'error': '#DA3633',
    'info': '#1F6FEB',
    
    # Border colors
    'border': '#30363D',
    'border_light': '#484F58',
    
    # KPI Card specific
    'kpi_positive': '#3FB950',      # Positive trend
    'kpi_negative': '#F85149',      # Negative trend
    'kpi_neutral': '#8B949E',       # No change
}

# Chart colors for matplotlib (bright colors for dark background)
CHART_COLORS = [
    '#58A6FF',  # Blue
    '#3FB950',  # Green
    '#F0883E',  # Orange
    '#A371F7',  # Purple
    '#39D5FF',  # Cyan
    '#F9E24E',  # Yellow
    '#FF7EB6',  # Pink
    '#F85149',  # Red
]

# Main Application Stylesheet
MAIN_STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['bg_dark']};
}}

QWidget {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 13px;
}}

/* Buttons */
QPushButton {{
    background-color: {COLORS['primary']};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
    min-height: 32px;
}}

QPushButton:hover {{
    background-color: {COLORS['primary_light']};
}}

QPushButton:pressed {{
    background-color: {COLORS['primary_dark']};
}}

QPushButton:disabled {{
    background-color: {COLORS['bg_elevated']};
    color: {COLORS['text_muted']};
}}

/* Secondary Button */
QPushButton[class="secondary"] {{
    background-color: {COLORS['bg_elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
}}

QPushButton[class="secondary"]:hover {{
    background-color: {COLORS['bg_light']};
    border-color: {COLORS['border_light']};
}}

/* Labels */
QLabel {{
    color: {COLORS['text_primary']};
    background-color: transparent;
}}

QLabel[class="title"] {{
    font-size: 24px;
    font-weight: 700;
    color: {COLORS['text_primary']};
}}

QLabel[class="subtitle"] {{
    font-size: 14px;
    color: {COLORS['text_secondary']};
}}

QLabel[class="kpi-value"] {{
    font-size: 28px;
    font-weight: 700;
    color: {COLORS['text_primary']};
}}

QLabel[class="kpi-label"] {{
    font-size: 12px;
    color: {COLORS['text_secondary']};
    text-transform: uppercase;
}}

/* ComboBox */
QComboBox {{
    background-color: {COLORS['bg_elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px 12px;
    min-height: 32px;
    min-width: 120px;
}}

QComboBox:hover {{
    border-color: {COLORS['primary']};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLORS['text_secondary']};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    selection-background-color: {COLORS['primary']};
    selection-color: white;
    outline: none;
}}

/* Date Edit */
QDateEdit {{
    background-color: {COLORS['bg_elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px 12px;
    min-height: 32px;
}}

QDateEdit:hover {{
    border-color: {COLORS['primary']};
}}

QDateEdit::drop-down {{
    border: none;
    width: 24px;
}}

QCalendarWidget {{
    background-color: {COLORS['bg_medium']};
}}

QCalendarWidget QToolButton {{
    color: {COLORS['text_primary']};
    background-color: {COLORS['bg_elevated']};
    border-radius: 4px;
    padding: 4px;
}}

QCalendarWidget QToolButton:hover {{
    background-color: {COLORS['primary']};
}}

QCalendarWidget QMenu {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
}}

QCalendarWidget QSpinBox {{
    background-color: {COLORS['bg_elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
}}

QCalendarWidget QWidget#qt_calendar_navigationbar {{
    background-color: {COLORS['bg_light']};
}}

QCalendarWidget QTableView {{
    background-color: {COLORS['bg_medium']};
    selection-background-color: {COLORS['primary']};
    selection-color: white;
}}

/* Table Widget */
QTableWidget {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    gridline-color: {COLORS['border']};
}}

QTableWidget::item {{
    padding: 8px;
    border-bottom: 1px solid {COLORS['border']};
}}

QTableWidget::item:selected {{
    background-color: {COLORS['primary']};
    color: white;
}}

QTableWidget::item:hover {{
    background-color: {COLORS['bg_light']};
}}

QHeaderView::section {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
    padding: 10px;
    border: none;
    border-bottom: 2px solid {COLORS['primary']};
    font-weight: 600;
}}

QTableWidget QTableCornerButton::section {{
    background-color: {COLORS['bg_light']};
    border: none;
}}

/* Scrollbars */
QScrollBar:vertical {{
    background-color: {COLORS['bg_dark']};
    width: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['bg_elevated']};
    min-height: 30px;
    border-radius: 6px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['border_light']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {COLORS['bg_dark']};
    height: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['bg_elevated']};
    min-width: 30px;
    border-radius: 6px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS['border_light']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* Splitter */
QSplitter::handle {{
    background-color: {COLORS['border']};
}}

QSplitter::handle:hover {{
    background-color: {COLORS['primary']};
}}

/* Frame */
QFrame {{
    background-color: {COLORS['bg_medium']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
}}

QFrame[class="card"] {{
    background-color: {COLORS['bg_medium']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 16px;
}}

QFrame[class="kpi-card"] {{
    background-color: {COLORS['bg_medium']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
}}

/* Message Box */
QMessageBox {{
    background-color: {COLORS['bg_medium']};
}}

QMessageBox QLabel {{
    color: {COLORS['text_primary']};
}}

/* Tool Tips */
QToolTip {{
    background-color: {COLORS['bg_elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px;
}}

/* Group Box */
QGroupBox {{
    background-color: {COLORS['bg_medium']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {COLORS['text_primary']};
}}

/* Line Edit */
QLineEdit {{
    background-color: {COLORS['bg_elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 20px;
}}

QLineEdit:focus {{
    border-color: {COLORS['primary']};
}}

QLineEdit:hover {{
    border-color: {COLORS['border_light']};
}}

/* Progress Bar */
QProgressBar {{
    background-color: {COLORS['bg_elevated']};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {COLORS['primary']};
    border-radius: 4px;
}}
"""

# Matplotlib style for dark theme with bright charts
def get_matplotlib_style():
    """Returns matplotlib rcParams for dark theme with bright charts."""
    return {
        # Figure
        'figure.facecolor': COLORS['bg_medium'],
        'figure.edgecolor': COLORS['bg_medium'],
        'figure.figsize': (10, 6),
        'figure.dpi': 100,
        
        # Axes
        'axes.facecolor': COLORS['bg_medium'],
        'axes.edgecolor': COLORS['border'],
        'axes.labelcolor': COLORS['text_primary'],
        'axes.titlecolor': COLORS['text_primary'],
        'axes.titlesize': 14,
        'axes.titleweight': 'bold',
        'axes.labelsize': 11,
        'axes.prop_cycle': f"cycler('color', {CHART_COLORS})",
        'axes.grid': True,
        'axes.axisbelow': True,
        'axes.spines.top': False,
        'axes.spines.right': False,
        
        # Grid
        'grid.color': COLORS['border'],
        'grid.linestyle': '--',
        'grid.linewidth': 0.5,
        'grid.alpha': 0.5,
        
        # Ticks
        'xtick.color': COLORS['text_secondary'],
        'ytick.color': COLORS['text_secondary'],
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        
        # Legend
        'legend.facecolor': COLORS['bg_light'],
        'legend.edgecolor': COLORS['border'],
        'legend.labelcolor': COLORS['text_primary'],
        'legend.fontsize': 10,
        
        # Text
        'text.color': COLORS['text_primary'],
        
        # Lines
        'lines.linewidth': 2.5,
        'lines.markersize': 8,
        
        # Bars
        'patch.edgecolor': 'none',
    }


def apply_matplotlib_style():
    """Apply the dark theme style to matplotlib."""
    import matplotlib.pyplot as plt
    style = get_matplotlib_style()
    for key, value in style.items():
        try:
            plt.rcParams[key] = value
        except (KeyError, ValueError):
            pass  # Skip invalid parameters


# KPI Card styles
KPI_CARD_STYLE = f"""
    QFrame {{
        background-color: {COLORS['bg_medium']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 0px;
    }}
    QFrame:hover {{
        border-color: {COLORS['primary']};
    }}
"""

KPI_VALUE_STYLE = f"""
    font-size: 28px;
    font-weight: 700;
    color: {COLORS['text_primary']};
    background-color: transparent;
    border: none;
"""

KPI_LABEL_STYLE = f"""
    font-size: 11px;
    font-weight: 600;
    color: {COLORS['text_secondary']};
    text-transform: uppercase;
    letter-spacing: 1px;
    background-color: transparent;
    border: none;
"""

KPI_TREND_POSITIVE = f"""
    font-size: 13px;
    font-weight: 600;
    color: {COLORS['kpi_positive']};
    background-color: transparent;
    border: none;
"""

KPI_TREND_NEGATIVE = f"""
    font-size: 13px;
    font-weight: 600;
    color: {COLORS['kpi_negative']};
    background-color: transparent;
    border: none;
"""

KPI_TREND_NEUTRAL = f"""
    font-size: 13px;
    font-weight: 600;
    color: {COLORS['kpi_neutral']};
    background-color: transparent;
    border: none;
"""

