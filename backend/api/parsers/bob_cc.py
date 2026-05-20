"""
Bank of Baroda Credit Card PDF parser (table-based).
Expects pdfplumber to extract a table with columns:
  Date | Description/Narration | Debit | Credit  (or similar)
"""
import io
from typing import Optional
import pdfplumber
import pandas as pd
import re


def _clean_amount(val: str) -> float:
    if not val or str(val).strip() in ("", "-", "nan"):
        return 0.0
    return float(re.sub(r"[₹,\s]", "", str(val)))


def parse_bob_statement(
    file_bytes: bytes,
    password: str = "",
) -> tuple[Optional[pd.DataFrame], str]:
    try:
        open_kw = {"password": password} if password else {}
        with pdfplumber.open(io.BytesIO(file_bytes), **open_kw) as pdf:
            tables = []
            for page in pdf.pages:
                for table in page.extract_tables():
                    tables.append(table)
    except Exception as e:
        return None, f"Could not open PDF: {e}"

    if not tables:
        return None, "No tables found in PDF"

    # Find the transaction table (must have a Date-like column)
    df_raw = None
    for table in tables:
        if len(table) < 3:
            continue
        header = [str(c).lower().strip() for c in (table[0] or [])]
        if any("date" in h for h in header):
            df_raw = pd.DataFrame(table[1:], columns=table[0])
            break

    if df_raw is None:
        return None, "Could not find transaction table in BOB PDF"

    df_raw.columns = [str(c).strip() for c in df_raw.columns]

    # Normalise column names
    col_map: dict[str, str] = {}
    for col in df_raw.columns:
        lc = col.lower()
        if "date" in lc and "col_date" not in col_map:
            col_map["col_date"] = col
        elif any(k in lc for k in ("narr", "desc", "particular", "detail")) and "col_desc" not in col_map:
            col_map["col_desc"] = col
        elif "debit" in lc and "col_debit" not in col_map:
            col_map["col_debit"] = col
        elif "credit" in lc and "col_credit" not in col_map:
            col_map["col_credit"] = col
        elif "amount" in lc and "col_amount" not in col_map:
            col_map["col_amount"] = col

    if "col_date" not in col_map:
        return None, "BOB parser: could not find Date column"

    rows = []
    for _, row in df_raw.iterrows():
        raw_date = str(row.get(col_map["col_date"], "")).strip()
        if not raw_date or raw_date.lower() == "nan":
            continue
        try:
            date = pd.to_datetime(raw_date, dayfirst=True, format="mixed").strftime("%Y-%m-%d")
        except Exception:
            continue

        desc = str(row.get(col_map.get("col_desc", ""), "")).strip()

        if "col_debit" in col_map:
            debit  = _clean_amount(row.get(col_map["col_debit"], ""))
            credit = _clean_amount(row.get(col_map.get("col_credit", ""), ""))
            if debit > 0:
                amount, txn_type = debit, "Debit"
            elif credit > 0:
                amount, txn_type = credit, "Credit"
            else:
                continue
        elif "col_amount" in col_map:
            amount = _clean_amount(row.get(col_map["col_amount"], ""))
            if amount == 0:
                continue
            txn_type = "Debit"
        else:
            continue

        rows.append({
            "Date": date,
            "Amount": amount,
            "Description": desc,
            "Payment Method": "Credit Card",
            "Type": txn_type,
        })

    if not rows:
        return None, "BOB parser: no valid rows extracted"

    return pd.DataFrame(rows), f"BOB CC: {len(rows)} transactions"
