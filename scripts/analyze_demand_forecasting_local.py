#!/usr/bin/env python3
"""Find the most expensive material and list concrete demands from local source tables."""

from __future__ import annotations

from pathlib import Path
import pandas as pd


DATA_SOURCE = Path(
    "external resources/Projects at Work/Celonis AI Demand Forecast App/"
    "celonis-mlwb/Subproject - Data Push Pipeline/data source"
)


def main() -> None:
    mbew = pd.read_csv(DATA_SOURCE / "MBEW.csv")
    makt = pd.read_csv(DATA_SOURCE / "MAKT.csv")
    pbed = pd.read_csv(DATA_SOURCE / "PBED.csv")

    # Unit price is not explicit in MBEW here; derive from stock value and quantity.
    mbew["UNIT_PRICE"] = mbew.apply(
        lambda row: (row["SALK3"] / row["LBKUM"]) if row["LBKUM"] else None,
        axis=1,
    )

    most_expensive = mbew.sort_values("UNIT_PRICE", ascending=False).iloc[0]
    matnr = str(most_expensive["MATNR"])

    name_series = makt[makt["MATNR"].astype(str) == matnr]["MAKTX"]
    material_name = name_series.iloc[0] if not name_series.empty else ""

    demands = pbed[pbed["MATNR"].astype(str) == matnr].sort_values("PDATU")

    print("MOST_EXPENSIVE_MATERIAL")
    print(
        {
            "MATNR": matnr,
            "MAKTX": material_name,
            "WERKS": most_expensive["WERKS"],
            "UNIT_PRICE": round(float(most_expensive["UNIT_PRICE"]), 6),
            "LBKUM": float(most_expensive["LBKUM"]),
            "SALK3": float(most_expensive["SALK3"]),
        }
    )

    print("\nCONCRETE_DEMANDS")
    print(f"count={len(demands)}")
    if demands.empty:
        print("No PBED demand rows found for this material.")
        return

    print(demands[["MATNR", "WERKS", "BDZEI", "PDATU", "MENGE"]].to_string(index=False))


if __name__ == "__main__":
    main()
