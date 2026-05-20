"""
Generic bank statement parser.
Strategy:
  1. Try to extract a table with pdfplumber.
  2. Find columns for Date, Description/Narration, Debit/Credit or Amount.
  3. Fall back to text-based line parsing if no table is found.
"""
import io
import re
from typing import Optional
import pdfplumber
import pandas as pd


_DATE_RE  = re.compile(r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}\s+\w{3}\s+\d{2,4})\b")
_AMOUNT_RE = re.compile(r"([\d,]+\.\d{2})")


def _clean_amount(val: str) -> float:
    try:
        return float(re.sub(r"[₹,\s]", "", str(val)))
    except Exception:
        return 0.0


def _parse_date(raw: str) -> Optional[str]:
    try:
        return pd.to_datetime(raw, dayfirst=True, format="mixed").strftime("%Y-%m-%d")
    except Exception:
        return None


def _table_parse(tables: list) -> Optional[pd.DataFrame]:
    for table in tables:
        if not table or len(table) < 3:
            continue
        header = [str(c).lower().strip() for c in (table[0] or [])]
        if not any("date" in h for h in header):
            continue

        df = pd.DataFrame(table[1:], columns=table[0])
        df.columns = [str(c).strip() for c in df.columns]

        col_map: dict[str, str] = {}
        for col in df.columns:
            lc = col.lower()
            if "date" in lc and "col_date" not in col_map:
                col_map["col_date"] = col
            elif any(k in lc for k in ("narr", "desc", "particular", "detail", "remark")) and "col_desc" not in col_map:
                col_map["col_desc"] = col
            elif "debit" in lc and "col_debit" not in col_map:
                col_map["col_debit"] = col
            elif "credit" in lc and "col_credit" not in col_map:
                col_map["col_credit"] = col
            elif "amount" in lc and "col_amount" not in col_map:
                col_map["col_amount"] = col

        if "col_date" not in col_map:
            continue

        rows = []
        for _, row in df.iterrows():
            raw_date = str(row.get(col_map["col_date"], "")).strip()
            date = _parse_date(raw_date)
            if not date:
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
                "Payment Method": "UPI",
                "Type": txn_type,
            })

        if rows:
            return pd.DataFrame(rows)

    return None


def _text_parse(pages_text: list[str]) -> Optional[pd.DataFrame]:
    """Last-resort line-by-line heuristic parser."""
    rows = []
    for text in pages_text:
        for line in text.splitlines():
            date_m = _DATE_RE.search(line)
            if not date_m:
                continue
            date = _parse_date(date_m.group(1))
            if not date:
                continue
            amounts = _AMOUNT_RE.findall(line)
            if not amounts:
                continue
            amount = _clean_amount(amounts[-1])
            if amount <= 0:
                continue
            # Remove date and amounts from line to get description
            desc = _DATE_RE.sub("", line)
            desc = _AMOUNT_RE.sub("", desc).strip(" -|,")
            rows.append({
                "Date": date,
                "Amount": amount,
                "Description": desc,
                "Payment Method": "UPI",
                "Type": "Debit",
            })

    return pd.DataFrame(rows) if rows else None


def parse_generic_statement(
    file_bytes: bytes,
    password: str = "",
) -> tuple[Optional[pd.DataFrame], str]:
    try:
        open_kw = {"password": password} if password else {}
        with pdfplumber.open(io.BytesIO(file_bytes), **open_kw) as pdf:
            tables = []
            pages_text = []
            for page in pdf.pages:
                pages_text.append(page.extract_text() or "")
                for table in page.extract_tables():
                    tables.append(table)
    except Exception as e:
        return None, f"Could not open PDF: {e}"

    df = _table_parse(tables)
    if df is not None and not df.empty:
        return df, f"Generic (table): {len(df)} transactions"

    df = _text_parse(pages_text)
    if df is not None and not df.empty:
        return df, f"Generic (text): {len(df)} transactions"

    return None, "Generic parser could not find any transactions in this PDF"
