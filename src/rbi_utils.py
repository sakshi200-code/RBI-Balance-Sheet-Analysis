from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


RAW_COLUMNS = {
    "Currency in circulation -Total": "currency_in_circulation",
    "`Other' deposits with RBI": "other_deposits_with_rbi",
    "Bankers' deposits with RBI": "bankers_deposits_with_rbi",
    "Reserve Money (Liabilities/Components)": "reserve_money",
    "RBI's Claims on - Government (net)": "claims_on_government_net",
    "RBI's Claims on - Central Govt": "claims_on_central_government",
    "RBI's Claims on Banks & Commercial sector": "claims_on_banks_and_commercial_sector",
    "RBI's Claims on Banks (Including NABARD)": "claims_on_banks_including_nabard",
    "RBI's claims on Commercial sector (Excluding NABARD)": "claims_on_commercial_sector_excluding_nabard",
    "Net foreign exchange assets of RBI": "net_foreign_exchange_assets",
    "Govt't currency liabilities to the public": "government_currency_liabilities_to_public",
    "Net non-monetary liabilities of RBI": "net_non_monetary_liabilities",
}

KEY_SERIES = [
    "reserve_money",
    "currency_in_circulation",
    "net_foreign_exchange_assets",
    "claims_on_government_net",
    "bankers_deposits_with_rbi",
]

BALANCE_SHEET_SERIES = list(RAW_COLUMNS.values())


def project_root() -> Path:
    cwd = Path.cwd()
    return cwd.parent if cwd.name == "notebooks" else cwd


def load_raw(path: str | Path | None = None) -> pd.DataFrame:
    path = Path(path) if path else project_root() / "data" / "raw" / "RBI_Data.xlsx"
    return pd.read_excel(path, sheet_name="Weekly", header=None)


def clean_rbi_data(path: str | Path | None = None) -> pd.DataFrame:
    raw = load_raw(path)
    header = raw.iloc[5].tolist()
    data = raw.iloc[7:].copy()
    data = data[data[1].notna()].copy()
    data = data[pd.to_datetime(data[1], errors="coerce").notna()].copy()
    cols = ["date"] + [RAW_COLUMNS.get(str(c).strip(), str(c).strip()) for c in header[2:14]]
    df = data.iloc[:, 1:14].copy()
    df.columns = cols
    df["date"] = pd.to_datetime(df["date"])
    for col in df.columns:
        if col != "date":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)
    return add_features(df)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    iso = df["date"].dt.isocalendar()
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.month_name()
    df["quarter"] = df["date"].dt.quarter
    df["week_number"] = iso.week.astype(int)
    df["financial_year"] = np.where(
        df["month"] >= 4,
        df["year"].astype(str) + "-" + (df["year"] + 1).astype(str).str[-2:],
        (df["year"] - 1).astype(str) + "-" + df["year"].astype(str).str[-2:],
    )
    df["is_month_end"] = df["date"].dt.is_month_end
    df["is_quarter_end"] = df["date"].dt.is_quarter_end
    for col in BALANCE_SHEET_SERIES:
        df[f"{col}_weekly_change"] = df[col].diff()
        df[f"{col}_weekly_growth_pct"] = df[col].pct_change() * 100
        df[f"{col}_mom_growth_pct"] = df[col].pct_change(4) * 100
        df[f"{col}_qoq_growth_pct"] = df[col].pct_change(13) * 100
        df[f"{col}_yoy_growth_pct"] = df[col].pct_change(52) * 100
        base = df[col].dropna().iloc[0] if df[col].notna().any() else np.nan
        df[f"{col}_index_base_100"] = df[col] / base * 100 if base else np.nan
        for window in [4, 8, 12, 26]:
            df[f"{col}_ma_{window}w"] = df[col].rolling(window).mean()
        df[f"{col}_rolling_std_12w"] = df[col].rolling(12).std()
        df[f"{col}_rolling_var_12w"] = df[col].rolling(12).var()
        df[f"{col}_rolling_median_12w"] = df[col].rolling(12).median()
        std = df[col].std()
        df[f"{col}_zscore"] = (df[col] - df[col].mean()) / std if std else np.nan
        if col != "reserve_money":
            df[f"{col}_pct_of_reserve_money"] = df[col] / df["reserve_money"] * 100
    return df


def load_cleaned(path: str | Path | None = None) -> pd.DataFrame:
    path = Path(path) if path else project_root() / "data" / "processed" / "cleaned_data.csv"
    df = pd.read_csv(path, parse_dates=["date"])
    return df


def save_figure(fig, name: str) -> Path:
    out = project_root() / "images" / name
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, dpi=160, bbox_inches="tight")
    return out


def mape(y_true, y_pred) -> float:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    mask = y_true != 0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)
