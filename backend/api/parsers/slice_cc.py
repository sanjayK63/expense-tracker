"""
Slice Credit Card PDF parser.
Handles both Format A (pre-April 2026) and Format B (April 2026+).

Format A:  MERCHANT ₹AMOUNT
           INITIAL
           DD MMM 'YY • METHOD

Format B:  MERCHANT AMOUNT
           [INITIAL] ₹
           DD MMM 'YY • METHOD
"""
import re
import io
from datetime import datetime
from typing import Optional
import pdfplumber
import pandas as pd


def _parse_date(raw: str) -> Optional[str]:
    raw = raw.strip().replace("'", "")
    for fmt in ("%d %b %Y", "%d %b %y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def parse_slice_statement(
    file_bytes: bytes,
    password: str = "",
) -> tuple[Optional[pd.DataFrame], str]:
    try:
        open_kw = {"password": password} if password else {}
        with pdfplumber.open(io.BytesIO(file_bytes), **open_kw) as pdf:
            pages_text = [p.extract_text() or "" for p in pdf.pages]
    except Exception as e:
        return None, f"Could not open PDF: {e}"

    all_text = "\n".join(pages_text)

    # Quick sanity check — Slice statements contain "SLICE" or "sliceit"
    if "slice" not in all_text.lower():
        return None, "Not a Slice statement"

    seen: set[tuple] = set()
    rows: list[dict] = []

    def _add_row(merchant: str, amount_str: str, date_raw: str, txn_type: str) -> None:
        date = _parse_date(date_raw)
        if not date:
            return
        amount = float(amount_str.replace(",", ""))
        key = (date, amount, merchant.strip(), txn_type)
        if key in seen:
            return
        seen.add(key)
        rows.append({
            "Date": date,
            "Amount": amount,
            "Description": merchant.strip(),
            "Payment Method": "Credit Card",
            "Type": txn_type,
        })

    # ── Format A debit: MERCHANT ₹AMOUNT \n INITIAL \n DATE • METHOD ────────
    for m in re.finditer(
        r"^(.+?)\s+₹([\d,]+(?:\.\d+)?)\s*$\n^[A-Za-z]\s*$\n^(\d{1,2}\s+\w{3}\s+'?\d{2,4})\s*[•·]\s*(\w+)",
        all_text, re.MULTILINE,
    ):
        _add_row(m.group(1), m.group(2), m.group(3), "Debit")

    # ── Format B debit: MERCHANT AMOUNT \n [INITIAL] ₹ \n DATE • METHOD ────
    for m in re.finditer(
        r"^(.+?)\s+([\d,]+(?:\.\d+)?)\s*$\n^(?:[A-Za-z]\s+)?₹\s*$\n^(\d{1,2}\s+\w{3}\s+'?\d{2,4})\s*[•·]\s*(\w+)",
        all_text, re.MULTILINE,
    ):
        _add_row(m.group(1), m.group(2), m.group(3), "Debit")

    # ── Format A credit: MERCHANT ₹AMOUNT \n DATE ───────────────────────────
    for m in re.finditer(
        r"^(.+?)\s+₹([\d,]+(?:\.\d+)?)\s*$\n^(\d{1,2}\s+\w{3}\s+'?\d{2,4})\s*$",
        all_text, re.MULTILINE,
    ):
        _add_row(m.group(1), m.group(2), m.group(3), "Credit")

    # ── Format B credit: MERCHANT AMOUNT \n ₹ \n DATE ───────────────────────
    for m in re.finditer(
        r"^(.+?)\s+([\d,]+(?:\.\d+)?)\s*$\n^₹\s*$\n^(\d{1,2}\s+\w{3}\s+'?\d{2,4})\s*$",
        all_text, re.MULTILINE,
    ):
        _add_row(m.group(1), m.group(2), m.group(3), "Credit")

    if not rows:
        return None, "Slice parser found no transactions"

    return pd.DataFrame(rows), f"Slice CC: {len(rows)} transactions"
