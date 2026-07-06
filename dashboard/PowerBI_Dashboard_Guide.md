# Power BI Dashboard Build Guide

Use the files in `data/processed/` as Power BI sources.

## Tables

- `cleaned_data.csv`: main fact table at weekly grain.
- `dashboard_kpis.csv`: latest KPI values for executive cards.
- `monthly_growth_summary.csv`: month-end growth table.
- `correlation_matrix.csv`: correlation heatmap source.

## Suggested Pages

1. Executive Summary: KPI cards for latest reserve money, weekly growth, net foreign exchange assets, and currency in circulation.
2. Trend Analysis: weekly line charts, rolling averages, and growth-rate views.
3. Correlation and Drivers: matrix heatmap, scatter plots, and regression summary outputs.
4. Volatility and Anomalies: rolling volatility, z-score anomaly flags, and event annotations.
5. Forecast: historical vs forecast lines with error metrics.

## Model

Use `date` from `cleaned_data.csv` as the main date key. Create or import a calendar table if you need fiscal-year slicing.

## Visual Style

Use a sober central-bank research style: light background, dark text, restrained RBI-inspired blue accents, and clear axis labels.
