#!/usr/bin/env python3
"""
werkzeuge/download_images_from_repo.py

Liest daten_quelle_naben.xlsx (im Repo-Root) und lädt Bilder pro Eintrag herunter.

Benötigte Pakete:
  pip install pandas openpyxl icrawler

Benutzung (im Repo-Root):
  python3 werkzeuge/download_images_from_repo.py \
    --excel daten_quelle_naben.xlsx \
    --outdir images_from_naben \
    --max 40

Optionen:
  --excel   Pfad zur Excel-Datei (default: daten_quelle_naben.xlsx)
  --sheet   Tabellenblattname (optional)
  --outdir  Ausgabeordner (default: images)
  --max     Max Bilder pro Suchbegriff (default: 50)
  --timeout Request-Timeout Sekunden (default: 10)

Das Skript versucht, typische Spaltennamen zu finden:
  Hersteller, Herstellername, Manufacturer, Marke
  Modell, Model, Name
Wenn solche Spalten nicht gefunden werden, werden alle Text-Spalten einer Zeile kombiniert.
"""

from __future__ import annotations
import argparse
import os
import sys
from typing import List
import pandas as pd
from icrawler.builtin import BingImageCrawler

# Mögliche Spaltennamen (Deutsch/Englisch)
VENDOR_COLS = ["Hersteller", "Herstellername", "Manufacturer", "Vendor", "Marke", "Brand"]
MODEL_COLS = ["Modell", "Model", "Name", "Bezeichnung", "Type"]


def find_column(df: pd.DataFrame, candidates: List[str]):
    for c in candidates:
        if c in df.columns:
            return c
    # case-insensitive match
    lc_cols = {col.lower(): col for col in df.columns}
    for c in candidates:
        if c.lower() in lc_cols:
            return lc_cols[c.lower()]
    return None


def sanitize(name: str) -> str:
    return "".join(c if c.isalnum() or c in " _-." else "_" for c in (name or "")).strip() or "unknown"


def build_query_from_row(row: pd.Series, vendor_col: str|None, model_col: str|None) -> str:
    parts = []
    if vendor_col and pd.notna(row.get(vendor_col, None)):
        parts.append(str(row[vendor_col]).strip())
    if model_col and pd.notna(row.get(model_col, None)):
        parts.append(str(row[model_col]).strip())
    if parts:
        return " ".join(parts)
    # fallback: combine all non-numeric text columns
    text_parts = []
    for col, val in row.items():
        if pd.isna(val):
            continue
        s = str(val).strip()
        if not s:
            continue
        # skip pure numbers
        if s.replace(".", "", 1).isdigit():
            continue
        text_parts.append(s)
    return " ".join(text_parts) if text_parts else ""


def main():
    parser = argparse.ArgumentParser(description="Bilder für Naben-Einträge aus Excel herunterladen.")
    parser.add_argument("--excel", default="daten_quelle_naben.xlsx", help="Excel-Datei mit Naben-Daten")
    parser.add_argument("--sheet", default=None, help="Tabellenblattname (optional)")
    parser.add_argument("--outdir", default="images", help="Ausgabeordner")
    parser.add_argument("--max", type=int, default=50, help="Maximale Anzahl Bilder pro Suchbegriff")
    parser.add_argument("--timeout", type=int, default=10, help="Timeout in Sekunden pro Request")
    args = parser.parse_args()

    if not os.path.isfile(args.excel):
        print(f"Excel-Datei nicht gefunden: {args.excel}", file=sys.stderr)
        sys.exit(1)

    try:
        df = pd.read_excel(args.excel, sheet_name=args.sheet)
    except Exception as e:
        print(f"Fehler beim Lesen der Excel-Datei: {e}", file=sys.stderr)
        sys.exit(1)

    vendor_col = find_column(df, VENDOR_COLS)
    model_col = find_column(df, MODEL_COLS)

    print("Gefundene Spalten -> Hersteller:", vendor_col, "Modell:", model_col)

    os.makedirs(args.outdir, exist_ok=True)

    total = len(df.index)
    for idx, row in df.iterrows():
        query = build_query_from_row(row, vendor_col, model_col).strip()
        if not query:
            # überspringen wenn keine brauchbare Query
            print(f"[{idx+1}/{total}] Keine Suchbegriffe in Zeile {idx+1}, übersprungen.")
            continue
        safe = sanitize(query)[:120]  # Begrenze Länge des Ordnernamens
        target = os.path.join(args.outdir, safe)
        os.makedirs(target, exist_ok=True)
        print(f"[{idx+1}/{total}] Suche: '{query}' → {target} (max {args.max})")
        crawler = BingImageCrawler(storage={'root_dir': target}, timeout=args.timeout)
        try:
            crawler.crawl(keyword=query, max_num=args.max)
        except Exception as e:
            print(f"Fehler beim Crawlen von '{query}': {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
