# Product Requirements Document (PRD)
# Business Intelligence Suite - Rechnungsanalyse-Tool

**Version:** 1.1.0  
**Letzte Aktualisierung:** 04.12.2024  
**Status:** In Entwicklung

---

## 📋 Inhaltsverzeichnis

1. [Produktübersicht](#produktübersicht)
2. [Architektur](#architektur)
3. [Dashboard 1: Einnahmenanalyse](#dashboard-1-einnahmenanalyse)
4. [Dashboard 2: Marketing-Analyse](#dashboard-2-marketing-analyse)
5. [Dashboard 3: Ausgabenanalyse](#dashboard-3-ausgabenanalyse)
6. [Cross-Dashboard Analyse](#cross-dashboard-analyse)
7. [Analytics Engine](#analytics-engine)
8. [Technische Spezifikationen](#technische-spezifikationen)
9. [Implementierungsplan](#implementierungsplan)
10. [Changelog](#changelog)

---

## 📦 Produktübersicht

### Vision
Eine vollständige Business Intelligence Suite zur Analyse von Einnahmen, Marketing-Performance und Ausgaben mit mathematischen Prognosen und regelbasierten Empfehlungen.

### Kernfunktionen
- **3 spezialisierte Dashboards** in einer Anwendung
- **PDF-Parsing** für automatische Datenextraktion (Einnahmen & Ausgaben)
- **Manueller Input** für Marketing-Daten
- **Periodenvergleich** über alle Dashboards
- **Mathematische Prognosen** ohne externe AI/LLM
- **Cross-Dashboard Profit-Analyse**
- **Regelbasierte Empfehlungen** für Effizienzsteigerung

### Zielgruppe
- Selbstständige und Kleinunternehmer
- Finanz- und Marketingverantwortliche
- Controller und Business Analysten

---

## 🏗️ Architektur

### Dateistruktur
```
Rechnungsanalysetool/
├── main.py                          # Hauptanwendung mit Tab-Navigation
├── PRD.md                           # Diese Dokumentation
│
├── dashboards/                      # Dashboard-Module
│   ├── __init__.py
│   ├── base_dashboard.py            # Abstrakte Basis-Klasse
│   ├── revenue_dashboard.py         # Einnahmen-Dashboard
│   ├── marketing_dashboard.py       # Marketing-Dashboard
│   └── expense_dashboard.py         # Ausgaben-Dashboard
│
├── analytics/                       # Analyse-Engine
│   ├── __init__.py
│   ├── forecasting.py               # Mathematische Prognosen
│   ├── profit_engine.py             # Profit-Berechnung
│   └── recommendations.py           # Regelbasierte Empfehlungen
│
├── parsers/                         # PDF-Parser
│   ├── __init__.py
│   ├── base_parser.py               # Basis-Parser-Klasse
│   ├── revisage_parser.py           # Revisage-Rechnungen (Einnahmen)
│   └── expense_parsers/             # Ausgaben-Parser
│       ├── generic_parser.py        # Generischer Parser
│       └── custom_parsers.py        # Spezifische Formate
│
├── data/                            # Datenpersistenz
│   ├── revenue.json                 # Einnahmen-Daten
│   ├── marketing.json               # Marketing-Daten
│   └── expenses.json                # Ausgaben-Daten
│
├── data_manager.py                  # Zentrale Datenverwaltung
├── ui_components.py                 # Wiederverwendbare UI-Komponenten
├── charts.py                        # Visualisierungen
├── styles.py                        # Dark Theme & Styling
└── requirements.txt                 # Dependencies
```

### Technologie-Stack
| Komponente | Technologie |
|------------|-------------|
| GUI Framework | PyQt6 |
| Datenverarbeitung | pandas, numpy |
| Visualisierung | matplotlib |
| PDF-Parsing | pdfplumber |
| Export | openpyxl (Excel), reportlab (PDF) |
| Persistenz | JSON |
| Prognosen | scipy, numpy (statistisch) |

---

## 📊 Dashboard 1: Einnahmenanalyse

### Status: ✅ Implementiert (v3.0.0)

### Datenquelle
- **PDF-Parsing** von Revisage-Rechnungen
- Automatische Extraktion: Datum, Nettobetrag, Rechnungsnummer, Lieferant

### Datenmodell
```python
{
    "Date": datetime,           # Rechnungsdatum
    "Amount": float,            # Nettobetrag (€)
    "Description": str,         # Rechnungsnummer
    "Source": str,              # PDF-Dateiname
    "Category": str,            # Kategorie
    "Vendor": str,              # Lieferant
    "Currency": str,            # Währung (EUR)
    "ID": str                   # Eindeutige ID
}
```

### Funktionen

#### KPI-Cards
| KPI | Beschreibung |
|-----|--------------|
| Gesamteinnahmen | Summe aller Einnahmen im Zeitraum |
| Ø Monatlich | Durchschnittliche monatliche Einnahmen |
| Höchster Monat | Monat mit höchsten Einnahmen |
| Jahresvergleich | YoY Wachstum in % |

#### Visualisierungen
- [x] Balkendiagramm (Monatlich/Jährlich)
- [x] Liniendiagramm mit Trend
- [x] Kreisdiagramm (Verteilung)
- [x] Donut-Diagramm
- [x] Heatmap (Monat × Jahr)
- [x] Gestapeltes Balkendiagramm
- [x] Periodenvergleich (2 Zeiträume)

#### Filter & Analyse
- [x] Zeitraum-Presets (Q1-Q4, Jahre, Monate)
- [x] Periodenvergleich mit Checkbox
- [x] Betragsfilter (Min/Max)
- [x] Drill-Down (Jahr → Monat → Rechnung)

#### Export
- [x] CSV-Export (deutsche Formatierung)
- [x] Excel-Export (formatiert)
- [x] PDF-Report

---

## 📈 Dashboard 2: Marketing-Analyse

### Status: 🔲 Geplant

### Datenquelle
- **Manueller Input** (keine API-Anbindung)
- Kampagnen-basierte Eingabe

### Datenmodell
```python
{
    "ID": str,                  # Eindeutige Kampagnen-ID
    "Campaign_Name": str,       # Kampagnenname
    "Platform": str,            # Plattform (Google Ads, Meta, etc.)
    "Start_Date": datetime,     # Startdatum
    "End_Date": datetime,       # Enddatum
    "Budget": float,            # Eingesetztes Budget (€)
    "Impressions": int,         # Impressionen
    "Clicks": int,              # Klicks
    "Conversions": int,         # Conversions
    "Revenue": float,           # Generierter Umsatz (€)
    "Notes": str                # Notizen
}
```

### Berechnete KPIs
| KPI | Formel | Beschreibung |
|-----|--------|--------------|
| **CTR** | Clicks / Impressions × 100 | Click-Through-Rate (%) |
| **CPC** | Budget / Clicks | Cost per Click (€) |
| **CPM** | Budget / Impressions × 1000 | Cost per Mille (€) |
| **CPA** | Budget / Conversions | Cost per Acquisition (€) |
| **ROAS** | Revenue / Budget | Return on Ad Spend |
| **Conversion Rate** | Conversions / Clicks × 100 | Konversionsrate (%) |

### Geplante Funktionen

#### Kampagnen-Management
- [ ] Kampagnen hinzufügen/bearbeiten/löschen
- [ ] Plattform-Kategorisierung (Google, Meta, LinkedIn, etc.)
- [ ] Zeitraum-basierte Eingabe
- [ ] Bulk-Import via CSV

#### KPI-Cards
- [ ] Gesamt-Budget (Zeitraum)
- [ ] Durchschnittlicher ROAS
- [ ] Beste Kampagne (nach ROAS)
- [ ] Gesamt-Conversions

#### Visualisierungen
- [ ] ROAS-Vergleich nach Kampagne
- [ ] Budget vs. Revenue Vergleich
- [ ] CTR-Trend über Zeit
- [ ] Plattform-Performance Vergleich
- [ ] Periodenvergleich (wie Einnahmen)

#### Analyse-Features
- [ ] Kampagnen-Ranking nach KPIs
- [ ] Zeitraum-Filter (Q1-Q4, Monate)
- [ ] Plattform-Filter
- [ ] Performance-Benchmarks

---

## 💸 Dashboard 3: Ausgabenanalyse

### Status: 🔲 Geplant

### Datenquelle
- **PDF-Parsing** verschiedener Rechnungsformate
- Konfigurierbare Parser für unterschiedliche Strukturen

### Datenmodell
```python
{
    "ID": str,                  # Eindeutige ID
    "Date": datetime,           # Rechnungsdatum
    "Amount": float,            # Nettobetrag (€)
    "VAT_Amount": float,        # MwSt.-Betrag (€)
    "Gross_Amount": float,      # Bruttobetrag (€)
    "Vendor": str,              # Lieferant
    "Category": str,            # Ausgabenkategorie
    "Description": str,         # Beschreibung
    "Source": str,              # PDF-Dateiname
    "Payment_Status": str,      # Bezahlt/Offen
    "Due_Date": datetime        # Fälligkeitsdatum (optional)
}
```

### Ausgaben-Kategorien
```python
EXPENSE_CATEGORIES = [
    "Betriebskosten",
    "Personal",
    "Marketing & Werbung",      # Verknüpfung zu Marketing-Dashboard
    "IT & Software",
    "Büro & Ausstattung",
    "Reisekosten",
    "Versicherungen",
    "Steuern & Abgaben",
    "Material & Waren",
    "Beratung & Dienstleistungen",
    "Miete & Nebenkosten",
    "Sonstiges"
]
```

### PDF-Parser Architektur
```python
class BaseExpenseParser:
    """Basis-Parser mit gemeinsamer Logik"""
    - extract_date()
    - extract_amounts()      # Netto, Brutto, MwSt.
    - extract_vendor()
    - extract_invoice_number()

class GenericParser(BaseExpenseParser):
    """Generischer Parser für unbekannte Formate"""
    - Muster-basierte Extraktion
    - Fallback-Logik

class CustomParser(BaseExpenseParser):
    """Template für spezifische Formate"""
    - Konfigurierbar via JSON
    - Regex-Patterns pro Feld
```

### Geplante Funktionen

#### PDF-Parsing
- [ ] Multi-Format Unterstützung
- [ ] Parser-Konfiguration via UI
- [ ] Lernfunktion für neue Formate
- [ ] Manuelle Korrektur bei Fehlern

#### KPI-Cards
- [ ] Gesamtausgaben (Zeitraum)
- [ ] Ø Monatliche Ausgaben
- [ ] Größte Ausgabenkategorie
- [ ] Offene Rechnungen

#### Visualisierungen
- [ ] Ausgaben nach Kategorie (Pie/Bar)
- [ ] Monatlicher Ausgabentrend
- [ ] Lieferanten-Ranking
- [ ] Periodenvergleich

---

## 🔄 Cross-Dashboard Analyse

### Status: 🔲 Geplant

### Profit-Berechnung
```
Profit = Einnahmen - Ausgaben

Marketing-bereinigter Profit = Einnahmen - (Ausgaben - Marketing-Budget)

Profit-Marge (%) = (Profit / Einnahmen) × 100
```

### Datenmodell
```python
{
    "Period": str,              # Zeitraum (z.B. "2024-Q1")
    "Revenue": float,           # Einnahmen
    "Expenses": float,          # Ausgaben (gesamt)
    "Marketing_Spend": float,   # Marketing-Budget
    "Marketing_Revenue": float, # Marketing-generierter Umsatz
    "Profit": float,            # Berechneter Profit
    "Profit_Margin": float,     # Profit-Marge (%)
    "ROAS_Overall": float       # Gesamt-ROAS
}
```

### Visualisierungen
- [ ] Profit-Timeline (Einnahmen vs. Ausgaben)
- [ ] Wasserfall-Diagramm (Einnahmen → Kosten → Profit)
- [ ] Kosten-Breakdown (Pie: Marketing, Betrieb, etc.)
- [ ] Profit-Trend mit Prognose
- [ ] Dashboard-Vergleichsmatrix

### Cross-Analyse Features
- [ ] Automatische Daten-Synchronisation
- [ ] Korrelationsanalyse (Marketing ↔ Einnahmen)
- [ ] Break-Even Berechnung
- [ ] Szenario-Planung ("Was-wäre-wenn")

---

## 🧮 Analytics Engine

### Mathematische Prognosen

#### 1. Lineare Regression
```python
def linear_forecast(data: pd.Series, periods: int) -> pd.Series:
    """
    Lineare Extrapolation basierend auf historischen Daten.
    
    Formel: y = mx + b
    - m: Steigung (Trend)
    - b: Y-Achsenabschnitt
    """
```

#### 2. Exponentielle Glättung
```python
def exponential_smoothing(data: pd.Series, alpha: float = 0.3) -> pd.Series:
    """
    Gewichtete Glättung mit Fokus auf neuere Daten.
    
    Formel: S_t = α × X_t + (1-α) × S_{t-1}
    - α: Glättungsfaktor (0-1)
    """
```

#### 3. Saisonale Analyse
```python
def seasonal_decomposition(data: pd.Series) -> dict:
    """
    Zerlegung in Trend, Saisonalität und Residuen.
    
    Rückgabe:
    - trend: Langfristiger Trend
    - seasonal: Monatliche Muster
    - residual: Zufällige Schwankungen
    """
```

#### 4. Moving Average Forecast
```python
def moving_average_forecast(data: pd.Series, window: int = 3) -> float:
    """
    Prognose basierend auf gleitendem Durchschnitt.
    """
```

#### 5. Wachstumsraten-Prognose
```python
def growth_rate_forecast(data: pd.Series, periods: int) -> pd.Series:
    """
    Prognose basierend auf durchschnittlicher Wachstumsrate.
    
    Formel: F_t = L × (1 + g)^t
    - L: Letzter bekannter Wert
    - g: Durchschnittliche Wachstumsrate
    """
```

### Regelbasierte Empfehlungen

#### Empfehlungs-Engine
```python
class RecommendationEngine:
    """
    Regelbasierte Empfehlungen ohne AI/LLM.
    100% deterministisch und nachvollziehbar.
    """
    
    RULES = {
        # Profit-Regeln
        "low_profit_margin": {
            "condition": "profit_margin < 10%",
            "severity": "high",
            "message": "Profit-Marge kritisch niedrig",
            "recommendation": "Kosten reduzieren oder Preise anpassen"
        },
        
        # Marketing-Regeln
        "high_marketing_ratio": {
            "condition": "marketing_spend / revenue > 25%",
            "severity": "medium",
            "message": "Marketing-Anteil überdurchschnittlich",
            "recommendation": "Marketing-Effizienz prüfen"
        },
        "low_roas": {
            "condition": "roas < 2.0",
            "severity": "high",
            "message": "ROAS unter Rentabilitätsgrenze",
            "recommendation": "Kampagnen optimieren oder pausieren"
        },
        
        # Ausgaben-Regeln
        "expense_growth_exceeds_revenue": {
            "condition": "expense_growth_rate > revenue_growth_rate",
            "severity": "high",
            "message": "Ausgaben wachsen schneller als Einnahmen",
            "recommendation": "Kostenkontrolle verstärken"
        },
        
        # Saisonale Regeln
        "seasonal_low_detected": {
            "condition": "current_month in seasonal_low_months",
            "severity": "info",
            "message": "Saisonales Tief erwartet",
            "recommendation": "Rücklagen für schwache Monate bilden"
        },
        
        # Trend-Regeln
        "declining_trend": {
            "condition": "trend_slope < -5%",
            "severity": "high",
            "message": "Negativer Trend erkannt",
            "recommendation": "Ursachenanalyse durchführen"
        }
    }
```

#### Empfehlungs-Ausgabe
```python
{
    "timestamp": datetime,
    "category": str,            # "profit", "marketing", "expense", "trend"
    "severity": str,            # "info", "low", "medium", "high"
    "title": str,               # Kurztitel
    "message": str,             # Detaillierte Nachricht
    "recommendation": str,      # Handlungsempfehlung
    "data_basis": dict,         # Zugrundeliegende Daten
    "confidence": float         # Konfidenz (0-1)
}
```

---

## ⚙️ Technische Spezifikationen

### Systemanforderungen
- **OS:** Windows 10/11, macOS 10.15+, Linux
- **Python:** 3.9+
- **RAM:** 4 GB (empfohlen: 8 GB)
- **Display:** 1920×1080 (empfohlen)

### Dependencies
```
PyQt6>=6.4.0
pandas>=2.0.0
numpy>=1.24.0
scipy>=1.10.0           # NEU: Für Prognosen
pdfplumber>=0.9.0
matplotlib>=3.7.0
openpyxl>=3.1.0
reportlab>=4.0.0
```

### Datenpersistenz
- **Format:** JSON (menschenlesbar, portabel)
- **Backup:** Automatisch bei Start (letzte 5 Versionen)
- **Export:** CSV, Excel, PDF

### Performance-Ziele
| Metrik | Ziel |
|--------|------|
| App-Start | < 3 Sekunden |
| PDF-Parsing (10 Dateien) | < 5 Sekunden |
| Chart-Rendering | < 500ms |
| Export (1000 Zeilen) | < 2 Sekunden |

---

## 📅 Implementierungsplan

### Phase 1: Analytics Engine ✅
**Status:** Implementiert (v3.1.0)
- [x] `analytics/forecasting.py` - Mathematische Prognosen
  - Lineare Regression
  - Exponentielle Glättung
  - Gleitender Durchschnitt
  - Wachstumsraten-Prognose
  - Kombinierte Prognose (gewichtet)
  - Saisonale Analyse
- [x] `analytics/recommendations.py` - Regelbasierte Empfehlungen
  - Trend-Analyse
  - Volatilitäts-Warnung
  - Konzentrations-Risiko
  - Saisonale Muster
  - Wachstums-Chancen
- [x] Integration in bestehendes Dashboard
- [x] Analytics-Panel mit Methoden-Auswahl
- [x] Empfehlungs-Cards mit Severity-Levels

### Phase 2: Architektur-Refactoring ⏳
**Geschätzter Aufwand:** 3-4 Stunden
- [ ] `dashboards/base_dashboard.py` - Abstrakte Basis
- [ ] `dashboards/revenue_dashboard.py` - Migration bestehender Code
- [ ] Tab-Navigation in `main.py`
- [ ] Gemeinsame UI-Komponenten extrahieren

### Phase 3: Marketing-Dashboard ⏳
**Geschätzter Aufwand:** 4-5 Stunden
- [ ] `dashboards/marketing_dashboard.py`
- [ ] Kampagnen-Eingabeformular
- [ ] KPI-Berechnungen (ROAS, CTR, etc.)
- [ ] Marketing-spezifische Charts
- [ ] Periodenvergleich-Integration

### Phase 4: Ausgaben-Dashboard ⏳
**Geschätzter Aufwand:** 5-6 Stunden
- [ ] `dashboards/expense_dashboard.py`
- [ ] `parsers/` - Multi-Format PDF-Parser
- [ ] Parser-Konfiguration UI
- [ ] Ausgaben-Kategorisierung
- [ ] Integration mit bestehendem System

### Phase 5: Cross-Dashboard Analyse ⏳
**Geschätzter Aufwand:** 4-5 Stunden
- [ ] `analytics/profit_engine.py`
- [ ] Profit-Berechnung & Visualisierung
- [ ] Korrelationsanalyse
- [ ] Gesamt-Empfehlungen
- [ ] Executive Summary View

### Phase 6: Polish & Testing ⏳
**Geschätzter Aufwand:** 2-3 Stunden
- [ ] UI/UX Verbesserungen
- [ ] Performance-Optimierung
- [ ] Desktop-App Packaging (PyInstaller)
- [ ] Dokumentation finalisieren

---

## 📝 Changelog

### [3.1.0] - 04.12.2024
#### Hinzugefügt
- Phase A: Analytics Engine
- `analytics/forecasting.py` mit 5 Prognosemethoden
- `analytics/recommendations.py` mit regelbasierten Empfehlungen
- Analytics-Panel im Dashboard (rechte Seite)
- Echtzeit-Prognosen mit Konfidenzbereich
- Empfehlungen nach Severity (Critical → Info)
- Prognose-Methoden-Auswahl in UI

### [3.0.0] - 04.12.2024
#### Hinzugefügt
- Phase 3: Such- und Filterfunktion
- Export-Funktionen (CSV, Excel, PDF)
- Kategorie-Tagging für Rechnungen
- Periodenvergleichs-Funktion

### [2.1.0] - 04.12.2024
#### Hinzugefügt
- Phase 2: Erweiterte Visualisierungen
- Pie/Donut Charts
- Heatmap (Monat × Jahr)
- Drill-Down Navigation
- Interaktive Tooltips

### [2.0.0] - 04.12.2024
#### Hinzugefügt
- Phase 1: Core Analytics
- KPI-Cards Dashboard
- Multi-select Date Range Filter
- Month-over-Month Vergleich
- Trendlinien

### [1.0.0] - Initial
- Basis PDF-Parsing
- Einfache Tabellenansicht
- Grundlegende Diagramme

---

## 🎯 Nächste Empfohlene Schritte

### Option A: ✅ Analytics Engine (ABGESCHLOSSEN)
- Mathematische Prognosen implementiert
- Regelbasierte Empfehlungen aktiv
- Analytics-Panel integriert

### Option B: Dashboard-Trennung
**Empfehlung: ⭐⭐⭐**
- Saubere Architektur für Erweiterungen
- Mehr initialer Aufwand
- Bessere Wartbarkeit langfristig
- Ermöglicht Tab-Navigation für 3 Dashboards

### Option C: Marketing-Dashboard
**Empfehlung: ⭐⭐⭐⭐⭐** ← Empfohlen als nächster Schritt
- Eigenständiges Modul
- Schnell implementierbar (manueller Input)
- Sofort nutzbar ohne PDF-Parser-Komplexität
- Verbindet sich später mit Cross-Dashboard Analyse

### Option D: Ausgaben-Dashboard
**Empfehlung: ⭐⭐⭐⭐**
- Multi-Format PDF-Parser erforderlich
- Komplexere Parser-Logik für verschiedene Rechnungsstrukturen
- Wichtig für vollständige Profit-Analyse

---

*Dieses Dokument wird automatisch aktualisiert, wenn neue Features implementiert werden.*

