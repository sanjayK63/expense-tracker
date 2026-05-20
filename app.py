import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import os
import uuid

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Expense Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Hide default sidebar page links */
    [data-testid="stSidebarNav"] { display: none; }

    /* Nav buttons */
    .stButton > button { border-radius: 8px; font-weight: 500; }

    /* KPI card */
    .kpi-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #0f3460;
        border-radius: 14px;
        padding: 1.1rem 1.4rem;
        text-align: center;
        color: #e0e0e0;
    }
    .kpi-card .label { font-size: 0.78rem; letter-spacing: .06em; opacity: .7; text-transform: uppercase; }
    .kpi-card .value { font-size: 1.65rem; font-weight: 700; margin: 4px 0 0 0; color: #fff; }
    .kpi-card .delta { font-size: 0.78rem; margin-top: 2px; }
    .kpi-positive { color: #4ecdc4; }
    .kpi-negative { color: #ff6b6b; }

    /* Budget bar */
    .bar-wrap { margin-bottom: 10px; }
    .bar-labels {
        display: flex; justify-content: space-between;
        font-size: 12px; margin-bottom: 3px; color: #555;
    }
    .bar-track {
        background: #e8ecf0; border-radius: 8px; height: 16px; overflow: hidden;
    }
    .bar-fill { height: 100%; border-radius: 8px; }

    /* Alert banner */
    .alert-over {
        background: #fff3f3; border-left: 4px solid #ff6b6b;
        padding: 8px 14px; border-radius: 6px; margin: 4px 0;
        font-size: 13px; color: #c0392b;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Constants ─────────────────────────────────────────────────────────────────
CATEGORIES = [
    "Food",
    "Transport",
    "Utilities",
    "Shopping & Health",
    "Entertainment & Education",
    "Investments & Savings",
    "Contra",
    "Trip",
    "Travel to Chennai",
    "Others",
]

CATEGORY_COLORS = {
    "Food": "#FF6B6B",
    "Transport": "#4ECDC4",
    "Utilities": "#45B7D1",
    "Shopping & Health": "#96CEB4",
    "Entertainment & Education": "#FECA57",
    "Investments & Savings": "#C39BD3",
    "Contra": "#76D7C4",
    "Trip": "#FFB347",
    "Travel to Chennai": "#F97F51",
    "Others": "#AAB7B8",
}

PAYMENT_METHODS = ["UPI", "Cash", "Credit Card", "Debit Card", "Net Banking", "Other"]

# keyword → category mapping used by the PDF-to-CSV auto-categoriser
KEYWORD_MAP: dict[str, list[str]] = {
    "Food": [
        "zomato", "swiggy", "food", "restaurant", "cafe", "coffee", "lunch", "dinner",
        "breakfast", "grocery", "supermarket", "superm", "blinkit", "bigbasket", "zepto",
        "dunzo", "dominos", "pizza", "burger", "kfc", "mcdonald", "subway", "dhaba",
        "canteen", "mess", "tiffin", "bakery", "sweet shop", "juice", "snack", "bake",
        "fresh mart", "fresh store", "fresh s", "n fresh", "provision", "vegetables",
        "fruits", "milk", "dairy", "halwa", "biryani", "thali", "hotel kitchen",
        "grand cafe", "hot box", "juice bar", "cool drinks", "tea shop", "tender coconut",
        "spicy", "tandoor", "idly", "dosa", "parota", "chai", "confectionery", "confecti",
        "mithai", "grand store", "grand market", "udupi", "murugan", "annapoorna",
        "family super", "family mart",
    ],
    "Transport": [
        "uber", "ola", "rapido", "petrol", "fuel", "diesel", "metro", "auto",
        "taxi", "cab", "toll", "fastag", "parking", "rickshaw", "local bus",
        "city bus", "bmtc", "best bus", "dtc", "apta", "mahanagar",
    ],
    "Utilities": [
        "electricity", "internet", "broadband", "mobile recharge", "recharge", "jio",
        "airtel", " vi ", "vodafone", "bsnl", "water bill", "gas bill", "piped gas",
        "lpg", "cylinder", "maintenance", "society", "rent", "emi", "bescom",
        "msedcl", "tata power", "adani electricity", "tangedco", "tneb", "kseb",
        "mescom", "gescom", "hescom", "cesc", "wbsedcl", "apepdcl",
    ],
    "Shopping & Health": [
        "amazon", "flipkart", "myntra", "meesho", "ajio", "nykaa", "firstcry",
        "pharmacy", "medical", "hospital", "doctor", "clinic", "medicine", "chemist",
        "health", "gym", "fitness", "yoga", "grooming", "salon", "spa", "barber",
        "apollo", "medplus", "netmeds", "1mg", "mr diy", "diy store",
        "supermarket", "hypermarket", "dmart", "reliance retail", "big bazaar",
    ],
    "Entertainment & Education": [
        "netflix", "prime video", "hotstar", "disney", "spotify", "youtube premium",
        "movie", "cinema", "pvr", "inox", "bookmyshow", "concert",
        "udemy", "coursera", "unacademy", "byju", "books", "kindle",
        "newspaper", "magazine", "subscription", "gaming", "steam",
        "ca monk", "camonk", "benchmarx", "academy", "coaching", "tuition",
        "icai", "institute", "school fees", "college fees", "exam fees",
        "study", "learning", "ca exam", "ca course",
    ],
    "Investments & Savings": [
        "sip", "mutual fund", " mf ", "stock", "equity", "zerodha", "groww", "upstox",
        "fixed deposit", " fd ", " rd ", "recurring deposit", "ppf", "nps",
        "insurance", "lic", "savings transfer", "investment",
        "smallcase", "coin by zerodha", "paytm money", "etmoney",
    ],
    "Contra": [
        "contra", "self transfer", "own account", "neft", "rtgs", "imps",
        "fund transfer", "wallet transfer", "repayment", "credit card repayment",
        "slice", "bob card", "hdfc card", "sbi card", "axis card",
    ],
    "Trip": [
        "oyo", "makemytrip", "cleartrip", "goibibo", "holiday", "vacation",
        "trip", "tour", "resort", "airbnb", "treebo", "hotel booking",
        # Train travel
        "irctc", "indian railway", "railway booking",
        # Long-distance bus (excluding Chennai-specific ones handled separately)
        "redbus", "orange tours",
        "neeta travels", "parveen travels", "setc", "ksrtc",
        "gsrtc", "apsrtc", "tsrtc", "msrtc", "upsrtc", "rsrtc",
        "state transport", "road transport",
        "karnataka transport", "karnatakasta", "karnatakastate",
        "kerala transport", "kerala state road", "kerala state",
        "tamil transport", "tamilnadu transport",
        "andhra transport", "andhra pradesh transport",
        # Flights
        "flight", "airline", "indigo", "spicejet", "air india", "vistara",
        "akasa", "airport", "aviation",
    ],
    "Travel to Chennai": [
        "tnstc", "zingbus", "abhibus",
    ],
}

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

EXPORT_FORMATS = ["CSV", "XLSX", "XLS", "XLSB"]

DATA_DIR          = os.path.join(os.path.dirname(__file__), "data")
EXPENSES_FILE     = os.path.join(DATA_DIR, "expenses.csv")
BUDGETS_FILE      = os.path.join(DATA_DIR, "budgets.csv")
ATTACHMENTS_DIR   = os.path.join(DATA_DIR, "attachments")
CUSTOM_KW_FILE    = os.path.join(DATA_DIR, "custom_keywords.csv")

# ── Data helpers ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=2)
def load_expenses() -> pd.DataFrame:
    if os.path.exists(EXPENSES_FILE):
        df = pd.read_csv(EXPENSES_FILE)
        df["date"]   = pd.to_datetime(df["date"], errors="coerce")
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
        if "attachment" not in df.columns:
            df["attachment"] = ""
        df["attachment"] = df["attachment"].fillna("")
        if "source" not in df.columns:
            df["source"] = ""
        df["source"] = df["source"].fillna("")
        return df
    return pd.DataFrame(columns=["id", "date", "amount", "category", "description", "payment_method", "attachment", "source"])


def save_expenses(df: pd.DataFrame):
    os.makedirs(DATA_DIR, exist_ok=True)
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out.to_csv(EXPENSES_FILE, index=False)
    load_expenses.clear()


@st.cache_data(ttl=2)
def load_budgets() -> pd.DataFrame:
    if os.path.exists(BUDGETS_FILE):
        df = pd.read_csv(BUDGETS_FILE)
        existing = set(df["category"])
        missing = [c for c in CATEGORIES if c not in existing]
        if missing:
            df = pd.concat(
                [df, pd.DataFrame({"category": missing, "monthly_limit": [0.0] * len(missing)})],
                ignore_index=True,
            )
        return df
    return pd.DataFrame({"category": CATEGORIES, "monthly_limit": [0.0] * len(CATEGORIES)})


def save_budgets(df: pd.DataFrame):
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(BUDGETS_FILE, index=False)
    load_budgets.clear()


@st.cache_data(ttl=2)
def load_custom_keywords() -> pd.DataFrame:
    if os.path.exists(CUSTOM_KW_FILE):
        df = pd.read_csv(CUSTOM_KW_FILE)
        # Ensure required columns exist
        for col in ("keyword", "category"):
            if col not in df.columns:
                df[col] = ""
        return df[["keyword", "category"]].dropna().copy()
    return pd.DataFrame(columns=["keyword", "category"])


def save_custom_keywords(df: pd.DataFrame):
    os.makedirs(DATA_DIR, exist_ok=True)
    df[["keyword", "category"]].to_csv(CUSTOM_KW_FILE, index=False)
    load_custom_keywords.clear()


def fmt(amount: float) -> str:
    return f"₹{amount:,.2f}"


def fmt_short(amount: float) -> str:
    if amount >= 1_00_000:
        return f"₹{amount/1_00_000:.2f}L"
    if amount >= 1_000:
        return f"₹{amount/1_000:.1f}K"
    return f"₹{amount:,.0f}"


# ── PDF extraction & auto-categorisation ─────────────────────────────────────
def detect_category(remark: str) -> str:
    if not remark or not str(remark).strip():
        return "Others"
    r = str(remark).lower()
    # Custom keywords take priority over built-in rules
    try:
        custom = load_custom_keywords()
        for _, row in custom.iterrows():
            kw  = str(row["keyword"]).strip().lower()
            cat = str(row["category"]).strip()
            if kw and cat and kw in r:
                return cat
    except Exception:
        pass
    # Fall back to built-in KEYWORD_MAP
    for cat, keywords in KEYWORD_MAP.items():
        if any(kw in r for kw in keywords):
            return cat
    return "Others"


def _exc_fingerprint(exc: Exception) -> str:
    """Combine all available text from an exception for reliable matching."""
    return " ".join([
        type(exc).__name__,
        str(exc),
        repr(exc),
    ]).lower()


def extract_pdf_tables(file_bytes: bytes, password: str = "") -> tuple:
    """Returns (DataFrame | None, status: str).
    Special statuses: 'PASSWORD_REQUIRED', 'WRONG_PASSWORD'.
    """
    import pdfplumber
    import io

    PASS_HINTS = (
        "password", "encrypt", "decrypt", "incorrect", "protected",
        "owner", "pdfpassword", "pdfencrypt", "not decrypted",
    )

    def _is_pass_error(exc: Exception) -> bool:
        return any(w in _exc_fingerprint(exc) for w in PASS_HINTS)

    def _clean(row: list) -> list:
        return [str(c).strip().replace("\n", " ") if c else "" for c in row]

    def _extract_tables(pdf) -> tuple[list, list | None]:
        all_rows: list = []
        headers: list | None = None
        for page in pdf.pages:
            for table in (page.extract_tables() or []):
                if not table or len(table) < 2:
                    continue
                if headers is None:
                    hdr = _clean(table[0])
                    headers = [h if h else f"Col{i}" for i, h in enumerate(hdr)]
                    data_rows = table[1:]
                else:
                    first = _clean(table[0])
                    data_rows = table[1:] if first == headers else table
                for row in data_rows:
                    cleaned = _clean(row)
                    if any(cleaned):
                        all_rows.append(cleaned)
        return all_rows, headers

    def _extract_text_fallback(pdf) -> tuple[list, list | None]:
        """Line-by-line text extraction when no tables are found."""
        lines = []
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                line = line.strip()
                if line:
                    lines.append(line)
        if not lines:
            return [], None
        # Split each line on 2+ consecutive spaces to get rough columns
        import re
        rows = [re.split(r" {2,}", ln) for ln in lines]
        max_cols = max(len(r) for r in rows)
        padded = [r + [""] * (max_cols - len(r)) for r in rows]
        headers = [f"Col{i}" for i in range(max_cols)]
        return padded, headers

    try:
        kwargs = {"password": password} if password else {}
        try:
            with pdfplumber.open(io.BytesIO(file_bytes), **kwargs) as pdf:
                all_rows, headers = _extract_tables(pdf)
                if not all_rows:
                    all_rows, headers = _extract_text_fallback(pdf)
                    if not all_rows:
                        return None, (
                            "No data could be extracted. The PDF may contain scanned images "
                            "rather than digital text. Try copying text from it manually."
                        )
                    extra = " *(text-mode — no tables found, columns auto-split)*"
                else:
                    extra = ""

        except Exception as exc:
            if _is_pass_error(exc):
                return None, "WRONG_PASSWORD" if password else "PASSWORD_REQUIRED"
            # Re-raise with full details so the outer handler can show them
            raise RuntimeError(
                f"{type(exc).__name__}: {str(exc) or repr(exc)}"
            ) from exc

        # Normalize every row to the same width as the widest row/header
        max_cols = max(len(headers), max((len(r) for r in all_rows), default=0))
        if max_cols > len(headers):
            headers = headers + [f"Col{i}" for i in range(len(headers), max_cols)]
        normalized = [(r + [""] * (max_cols - len(r)))[:max_cols] for r in all_rows]

        df = pd.DataFrame(normalized, columns=headers)
        df = df.replace("", pd.NA).dropna(how="all").fillna("")
        return df, f"Extracted **{len(df)} rows** × **{len(df.columns)} columns**{extra}."

    except Exception as exc:
        detail = str(exc) or repr(exc) or type(exc).__name__
        return None, f"Extraction error: {detail}"


def parse_merged_cell_statement(file_bytes: bytes, password: str = "") -> tuple:
    """
    Handles credit-card PDFs (e.g. Bank of Baroda) where every column in the
    transaction table is a single merged cell with all values newline-separated.
    Returns (DataFrame | None, message: str)
    """
    import pdfplumber, io, re

    PASS_HINTS = ("password", "encrypt", "decrypt", "incorrect", "protected",
                  "owner", "pdfpassword", "pdfencrypt", "not decrypted")

    all_txns: list = []
    try:
        kwargs = {"password": password} if password else {}
        with pdfplumber.open(io.BytesIO(file_bytes), **kwargs) as pdf:
            for page in pdf.pages:
                for table in (page.extract_tables() or []):
                    if not table or "Transaction Details" not in str(table[0]):
                        continue
                    for row in table:
                        if not row[0] or not re.search(r"\d{2}/\d{2}/\d{4}", str(row[0])):
                            continue
                        split = lambda cell: [
                            x.strip() for x in str(cell or "").split("\n") if x.strip()
                        ]
                        dates   = [x for x in split(row[0]) if re.match(r"\d{2}/\d{2}/\d{4}", x)]
                        refs    = split(row[1]) if len(row) > 1 else []
                        descs   = split(row[2]) if len(row) > 2 else []
                        amt_col = row[6] if len(row) > 6 else (row[-1] if row else None)
                        amt_raw = split(amt_col)

                        amounts, types = [], []
                        for a in amt_raw:
                            t = "Credit" if "CR" in a.upper() else "Debit"
                            n = re.sub(r"[^\d.]", "", a.replace(",", ""))
                            try:
                                amounts.append((float(n), t))
                            except ValueError:
                                pass

                        # Drop cardholder-name lines (PRIMARY CARD pattern)
                        txn_descs = [d for d in descs if not re.match(r"^[A-Z ]+\(PRIMARY CARD", d)]
                        n = min(len(dates), len(refs) or 9999, len(txn_descs), len(amounts))

                        for i in range(n):
                            amt, typ = amounts[i]
                            desc = txn_descs[i]
                            all_txns.append({
                                "Date":        dates[i],
                                "Ref No":      refs[i] if i < len(refs) else "",
                                "Description": desc,
                                "Amount":      amt,
                                "Type":        typ,
                            })

    except Exception as exc:
        fp = _exc_fingerprint(exc)
        if any(w in fp for w in PASS_HINTS):
            return None, "WRONG_PASSWORD" if password else "PASSWORD_REQUIRED"
        return None, None  # signal: not this format

    if not all_txns:
        return None, None  # signal: not this format

    df = pd.DataFrame(all_txns)
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce").dt.strftime("%Y-%m-%d")
    df["Remarks"]        = ""
    df["Category"]       = df["Description"].apply(detect_category)
    df["Payment Method"] = df["Description"].apply(
        lambda d: "UPI" if "UPI" in d.upper() else "Other"
    )
    return df, f"{len(df)} transactions · {int((df['Type']=='Debit').sum())} debits · {int((df['Type']=='Credit').sum())} credits"


def parse_slice_statement(file_bytes: bytes, password: str = "") -> tuple:
    """
    Parses Slice credit card statement PDFs (handles both format variants).

    Format A (older months — ₹ on line 1):
        MERCHANT ₹AMOUNT
        [single letter initial]
        DD Mon 'YY • METHOD

    Format B (newer months — ₹ on line 2):
        MERCHANT AMOUNT
        [initial] ₹   (or just  ₹  when no initial)
        DD Mon 'YY • METHOD

    Credit/cashback Format A:  MERCHANT ₹AMOUNT / DD Mon 'YY
    Credit/cashback Format B:  MERCHANT AMOUNT  / ₹ / DD Mon 'YY

    Returns (DataFrame | None, message) — None means not this format.
    """
    import pdfplumber, io, re

    PASS_HINTS = ("password", "encrypt", "decrypt", "incorrect", "protected",
                  "owner", "pdfpassword", "pdfencrypt", "not decrypted")

    SKIP_RE = re.compile(
        r"(?i)^(spends?|refunds?|cashback|interest|surcharge|statement|total|"
        r"min\s+amount|balance|carry|gst|igst|cgst|sgst|monies|earned|glossary|"
        r"payment\s+obligation|credit\s+card\s+security|bank\s+transfer)"
    )

    try:
        kwargs = {"password": password} if password else {}
        with pdfplumber.open(io.BytesIO(file_bytes), **kwargs) as pdf:
            page1_text = (pdf.pages[0].extract_text() or "").lower()
            if "credit card statement" not in page1_text or not any(
                kw in page1_text for kw in ("repay", "min amount due", "total amount due")
            ):
                return None, None  # not a Slice statement
            all_text = "\n".join((page.extract_text() or "") for page in pdf.pages)
    except Exception as exc:
        fp = _exc_fingerprint(exc)
        if any(w in fp for w in PASS_HINTS):
            return None, "WRONG_PASSWORD" if password else "PASSWORD_REQUIRED"
        return None, None

    rows = []
    seen: set = set()

    def _parse_date(raw: str) -> str:
        clean = raw.strip().replace("'", "20")
        try:
            return pd.to_datetime(clean, format="%d %b %Y").strftime("%Y-%m-%d")
        except Exception:
            return clean

    def _add_row(merchant, amount_str, date_raw, method_raw, txn_type):
        if SKIP_RE.match(merchant):
            return
        try:
            amount = float(amount_str.replace(",", ""))
        except ValueError:
            return
        if amount <= 0:
            return
        date_fmt   = _parse_date(date_raw)
        pay_method = "Credit Card" if str(method_raw).lower() == "card" else "UPI"
        key = (date_fmt, amount, merchant.rstrip("…").strip(), txn_type)
        if key in seen:
            return
        seen.add(key)
        rows.append({
            "Date":           date_fmt,
            "Amount":         amount,
            "Description":    merchant.rstrip("…").strip(),
            "Type":           txn_type,
            "Remarks":        "",
            "Category":       detect_category(merchant) if txn_type == "Debit" else "Contra",
            "Payment Method": pay_method,
        })

    # ── Format A spends: MERCHANT ₹AMOUNT / INITIAL / DATE • METHOD ──────────
    for m in re.finditer(
        r"^(.+?)\s+₹([\d,]+(?:\.\d+)?)\s*$\n"
        r"^[A-Za-z]\s*$\n"
        r"^(\d{1,2}\s+\w{3}\s+'?\d{2,4})\s*[•·]\s*(\w+)",
        all_text, re.MULTILINE,
    ):
        _add_row(m.group(1).strip(), m.group(2), m.group(3), m.group(4), "Debit")

    # ── Format B spends: MERCHANT AMOUNT / [INITIAL] ₹ / DATE • METHOD ──────
    for m in re.finditer(
        r"^(.+?)\s+([\d,]+(?:\.\d+)?)\s*$\n"
        r"^(?:[A-Za-z]\s+)?₹\s*$\n"
        r"^(\d{1,2}\s+\w{3}\s+'?\d{2,4})\s*[•·]\s*(\w+)",
        all_text, re.MULTILINE,
    ):
        _add_row(m.group(1).strip(), m.group(2), m.group(3), m.group(4), "Debit")

    # ── Format A credits: MERCHANT ₹AMOUNT / DATE ─────────────────────────────
    for m in re.finditer(
        r"^(.+?)\s+₹([\d,]+(?:\.\d+)?)\s*$\n"
        r"^(\d{1,2}\s+\w{3}\s+'?\d{2,4})\s*$",
        all_text, re.MULTILINE,
    ):
        _add_row(m.group(1).strip(), m.group(2), m.group(3), "Credit Card", "Credit")

    # ── Format B credits: MERCHANT AMOUNT / ₹ / DATE ─────────────────────────
    for m in re.finditer(
        r"^(.+?)\s+([\d,]+(?:\.\d+)?)\s*$\n"
        r"^₹\s*$\n"
        r"^(\d{1,2}\s+\w{3}\s+'?\d{2,4})\s*$",
        all_text, re.MULTILINE,
    ):
        _add_row(m.group(1).strip(), m.group(2), m.group(3), "Credit Card", "Credit")

    if not rows:
        return None, None

    df = pd.DataFrame(rows).sort_values("Date").reset_index(drop=True)
    n_d = int((df["Type"] == "Debit").sum())
    n_c = int((df["Type"] == "Credit").sum())
    return df, f"Slice CC · {len(df)} transactions · {n_d} debits · {n_c} credits"


def auto_parse_statement(raw: pd.DataFrame) -> tuple:
    """
    Automatically detect Date / Amount / Description columns from any bank
    statement DataFrame and return a clean (date, description, amount, type)
    DataFrame without any manual mapping.
    Returns (clean_df | None, message: str)
    """
    import re

    DATE_RE = re.compile(
        r"\b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}\b"          # 01/01/2024
        r"|\b\d{4}[/\-\.]\d{2}[/\-\.]\d{2}\b"                 # 2024-01-01
        r"|\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}\b"
        r"|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b",
        re.IGNORECASE,
    )

    def _clean_num(s: str) -> str:
        return re.sub(r"[₹$,\s]", "", s).rstrip("DrCrDRCR").strip()

    def _date_score(col):
        vals = raw[col].astype(str).str.strip()
        non_empty = vals[vals != ""]
        if len(non_empty) == 0:
            return 0.0
        return sum(bool(DATE_RE.search(v)) for v in non_empty) / len(non_empty)

    def _amount_score(col):
        vals = raw[col].astype(str).str.strip()
        non_empty = vals[vals != ""]
        if len(non_empty) == 0:
            return 0.0
        hits = sum(
            bool(re.match(r"^\d[\d,\.]*$", _clean_num(v))) for v in non_empty if _clean_num(v)
        )
        return hits / len(non_empty)

    def _avg_len(col):
        return raw[col].astype(str).str.strip().str.len().mean()

    cols = list(raw.columns)
    scores = {c: {"date": _date_score(c), "amt": _amount_score(c), "len": _avg_len(c)} for c in cols}

    # ── Pick date column ──────────────────────────────────────────────────────
    date_col = max(cols, key=lambda c: scores[c]["date"])
    if scores[date_col]["date"] < 0.25:
        date_col = None

    # ── Pick amount columns (score > 0.25, excluding date col) ───────────────
    amt_candidates = sorted(
        [(c, scores[c]["amt"]) for c in cols if c != date_col and scores[c]["amt"] > 0.25],
        key=lambda x: -x[1],
    )

    if not amt_candidates:
        return None, "Could not detect any numeric Amount column in the extracted data."

    # ── Pick description column (longest text, not date/amount) ──────────────
    used = {date_col} | {c for c, _ in amt_candidates}
    remaining = [c for c in cols if c not in used]
    desc_col = max(remaining, key=lambda c: scores[c]["len"]) if remaining else None

    # ── Build clean DataFrame ─────────────────────────────────────────────────
    out = pd.DataFrame()

    # Date
    if date_col:
        out["Date"] = pd.to_datetime(
            raw[date_col].astype(str), dayfirst=True, errors="coerce"
        ).dt.strftime("%Y-%m-%d")
    else:
        out["Date"] = ""

    # Description
    out["Description"] = raw[desc_col].astype(str).str.strip() if desc_col else ""

    # Amount — handle 1-column, 2-column (debit/credit), 3-column (debit/credit/balance)
    if len(amt_candidates) == 1:
        c = amt_candidates[0][0]
        out["Amount"] = pd.to_numeric(
            raw[c].astype(str).apply(_clean_num), errors="coerce"
        ).abs()
        out["Type"] = "Debit"
    else:
        # First two highest-scoring columns → treat as Debit & Credit
        dc, cc = amt_candidates[0][0], amt_candidates[1][0]
        debit = pd.to_numeric(raw[dc].astype(str).apply(_clean_num), errors="coerce").fillna(0).abs()
        credit = pd.to_numeric(raw[cc].astype(str).apply(_clean_num), errors="coerce").fillna(0).abs()
        out["Amount"] = debit.where(debit > 0, credit)
        out["Type"] = "Debit"
        out.loc[(debit == 0) & (credit > 0), "Type"] = "Credit"

    # Drop rows with no usable amount or date
    out = out[out["Amount"].notna() & (out["Amount"] > 0)].reset_index(drop=True)

    if out.empty:
        return None, "All rows were filtered out — no valid amounts found after parsing."

    # Add editable columns
    out["Remarks"]        = ""
    out["Category"]       = "Others"
    out["Payment Method"] = "Other"

    n_debit  = int((out["Type"] == "Debit").sum())
    n_credit = int((out["Type"] == "Credit").sum())
    note = f"{len(out)} transactions · {n_debit} debits · {n_credit} credits"
    return out, note


# ── Attachment helpers ────────────────────────────────────────────────────────
def save_attachment(expense_id: str, file_bytes: bytes) -> str:
    os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
    filename = f"{expense_id}.pdf"
    with open(os.path.join(ATTACHMENTS_DIR, filename), "wb") as f:
        f.write(file_bytes)
    return filename


def delete_attachment(filename: str):
    if filename:
        path = os.path.join(ATTACHMENTS_DIR, filename)
        if os.path.exists(path):
            os.remove(path)


def read_attachment(filename: str) -> bytes | None:
    if filename:
        path = os.path.join(ATTACHMENTS_DIR, filename)
        if os.path.exists(path):
            with open(path, "rb") as f:
                return f.read()
    return None


# ── Multi-format export ───────────────────────────────────────────────────────
def export_df_bytes(df: pd.DataFrame, fmt: str) -> tuple:
    """
    Returns (bytes, mime_type, file_extension, warning_msg | None).
    Supports CSV, XLSX, XLS, XLSB.
    """
    import io

    if fmt == "CSV":
        return (
            df.to_csv(index=False).encode("utf-8"),
            "text/csv", "csv", None,
        )

    if fmt == "XLSX":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            df.to_excel(w, index=False, sheet_name="Data")
        return (
            buf.getvalue(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "xlsx", None,
        )

    if fmt == "XLS":
        try:
            import xlwt  # noqa: PLC0415
            wb = xlwt.Workbook(encoding="utf-8")
            ws = wb.add_sheet("Data")
            for ci, col in enumerate(df.columns):
                ws.write(0, ci, str(col))
            for ri, row in enumerate(df.itertuples(index=False), start=1):
                for ci, val in enumerate(row):
                    try:
                        ws.write(ri, ci, val)
                    except Exception:
                        ws.write(ri, ci, str(val))
            buf = io.BytesIO()
            wb.save(buf)
            return (buf.getvalue(), "application/vnd.ms-excel", "xls", None)
        except ImportError:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                df.to_excel(w, index=False, sheet_name="Data")
            return (
                buf.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "xlsx",
                "xlwt not installed — file saved as XLSX instead.",
            )

    if fmt == "XLSB":
        import tempfile, os as _os  # noqa: PLC0415
        try:
            import pythoncom, win32com.client  # noqa: PLC0415
            pythoncom.CoInitialize()

            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
                xlsx_path = f.name
            xlsb_path = xlsx_path.replace(".xlsx", ".xlsb")

            df.to_excel(xlsx_path, index=False, engine="openpyxl")

            xl = win32com.client.Dispatch("Excel.Application")
            xl.DisplayAlerts = False
            xl.Visible = False
            try:
                wb = xl.Workbooks.Open(_os.path.abspath(xlsx_path))
                wb.SaveAs(_os.path.abspath(xlsb_path), 50)  # 50 = xlExcelBinaryWorkbook
                wb.Close(False)
            finally:
                xl.Quit()

            with open(xlsb_path, "rb") as f:
                data = f.read()
            for p in (xlsx_path, xlsb_path):
                try:
                    _os.remove(p)
                except OSError:
                    pass
            return (
                data,
                "application/vnd.ms-excel.sheet.binary.macroEnabled.12",
                "xlsb", None,
            )
        except Exception as exc:
            # Graceful fallback to XLSX
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                df.to_excel(w, index=False, sheet_name="Data")
            return (
                buf.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "xlsx",
                f"XLSB requires Microsoft Excel to be installed ({type(exc).__name__}) — saved as XLSX.",
            )

    raise ValueError(f"Unknown export format: {fmt}")


# ── Sidebar navigation ────────────────────────────────────────────────────────
PAGES = {
    "📊 Dashboard": "Dashboard",
    "➕ Add Expense": "Add Expense",
    "📂 Import CSV": "Import CSV",
    "🔄 PDF to CSV": "PDF to CSV",
    "🎯 Budget Settings": "Budget Settings",
    "📋 Transaction History": "Transaction History",
}

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

with st.sidebar:
    st.markdown("## 💰 Expense Tracker")
    st.caption("Monthly · INR ₹")
    st.markdown("---")
    for label, key in PAGES.items():
        is_active = st.session_state.page == key
        if st.button(label, key=f"nav_{key}", use_container_width=True,
                     type="primary" if is_active else "secondary"):
            st.session_state.page = key
            st.rerun()
    st.markdown("---")
    st.caption(f"Today: {date.today().strftime('%d %b %Y')}")

page = st.session_state.page


# ══════════════════════════════════════════════════════════════════════════════
# PAGE ▶ DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "Dashboard":
    st.title("📊 Monthly Expense Dashboard")

    df      = load_expenses()
    budgets = load_budgets()

    # ── Month / Year selector ──────────────────────────────────────────────
    cy = datetime.now().year
    cm = datetime.now().month
    sel_col1, sel_col2, _ = st.columns([2, 2, 6])
    sel_month = sel_col1.selectbox("Month", MONTHS, index=cm - 1, key="dash_month")
    year_opts = list(range(2022, cy + 2))
    sel_year  = sel_col2.selectbox("Year", year_opts, index=year_opts.index(cy), key="dash_year")
    month_num = MONTHS.index(sel_month) + 1

    # ── Filter to selected month (all transactions) ───────────────────────
    if not df.empty:
        mdf = df[(df["date"].dt.month == month_num) & (df["date"].dt.year == sel_year)].copy()
    else:
        mdf = pd.DataFrame(columns=df.columns if hasattr(df, "columns") else
                           ["id","date","amount","category","description","payment_method"])

    # Categories that are ALWAYS excluded from spend (financial flows, not real expenses).
    # Checked case-insensitively against the category value in the data.
    NON_SPEND_PATTERNS = (
        "contra", "transfer", "repayment", "refund", "interest received",
        "credit card repayment", "cashback", "reversal", "wallet load",
    )

    def _is_non_spend(cat: str) -> bool:
        c = str(cat).lower()
        return any(p in c for p in NON_SPEND_PATTERNS)

    spend_mdf = mdf[~mdf["category"].apply(_is_non_spend)] if not mdf.empty else mdf

    # ── Category selector — drives ALL numbers below ───────────────────────
    st.markdown("### Overview")
    available_cats = sorted(spend_mdf["category"].unique().tolist()) if not spend_mdf.empty else []
    sel_pie_cats = st.multiselect(
        "Categories shown in chart & overview",
        options=available_cats,
        default=available_cats,
        key="dash_pie_cats",
    )
    chart_mdf = spend_mdf[spend_mdf["category"].isin(sel_pie_cats)] if sel_pie_cats else spend_mdf

    # KPI values:
    # • Total Spent  = all selected categories
    # • Total Budget = sum of limits for selected categories that have a budget > 0
    # • Remaining    = budget vs spending for those same budgeted categories only
    #   (avoids comparing Food-only budget against total spending across all categories)
    total_spent = float(chart_mdf["amount"].sum()) if not chart_mdf.empty else 0.0
    txn_count   = len(chart_mdf)

    sel_budgets    = budgets[budgets["category"].isin(sel_pie_cats)] if sel_pie_cats else budgets
    budgeted_cats  = sel_budgets[sel_budgets["monthly_limit"] > 0]["category"].tolist()
    total_budget   = float(sel_budgets[sel_budgets["monthly_limit"] > 0]["monthly_limit"].sum())
    budget_spent   = float(chart_mdf[chart_mdf["category"].isin(budgeted_cats)]["amount"].sum()) if budgeted_cats else 0.0
    remaining      = total_budget - budget_spent

    # ── Over-budget alerts ─────────────────────────────────────────────────
    if not chart_mdf.empty and total_budget > 0:
        cat_spent_map = chart_mdf.groupby("category")["amount"].sum()
        for _, row in sel_budgets[sel_budgets["monthly_limit"] > 0].iterrows():
            spent = float(cat_spent_map.get(row["category"], 0))
            if spent > row["monthly_limit"]:
                st.markdown(
                    f'<div class="alert-over">⚠️ <b>{row["category"]}</b> exceeded budget — '
                    f'spent {fmt(spent)} vs limit {fmt(row["monthly_limit"])}</div>',
                    unsafe_allow_html=True,
                )

    # ── KPI cards ──────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)

    def kpi(col, label, value, delta_html=""):
        col.markdown(
            f'<div class="kpi-card"><div class="label">{label}</div>'
            f'<div class="value">{value}</div>{delta_html}</div>',
            unsafe_allow_html=True,
        )

    kpi(k1, "Total Spent", fmt(total_spent))
    if total_budget > 0:
        budgeted_label = " · ".join(budgeted_cats) if len(budgeted_cats) <= 3 else f"{len(budgeted_cats)} categories"
        kpi(k2, "Budget (tracked)", fmt(total_budget),
            f'<div class="delta" style="opacity:.6">{budgeted_label}</div>')
        pct = remaining / total_budget * 100
        cls = "kpi-positive" if remaining >= 0 else "kpi-negative"
        kpi(k3, "Remaining", fmt(remaining),
            f'<div class="delta {cls}">{pct:.1f}% of budget left</div>')
    else:
        kpi(k2, "Total Budget", "Not set")
        kpi(k3, "Remaining", "Set budget")

    top_cat = (
        chart_mdf.groupby("category")["amount"].sum().idxmax()
        if not chart_mdf.empty else "—"
    )
    kpi(k4, "Transactions", str(txn_count),
        f'<div class="delta" style="opacity:.6">Top: {top_cat}</div>')

    st.markdown("---")

    if not spend_mdf.empty:

        left_col, right_col = st.columns([1, 1])

        # ── Donut chart ────────────────────────────────────────────────────
        with left_col:
            st.markdown("#### Spending by Category")
            cat_totals = chart_mdf.groupby("category")["amount"].sum().reset_index()
            cat_totals.columns = ["Category", "Amount"]
            cat_totals = cat_totals.sort_values("Amount", ascending=False)
            colors = [CATEGORY_COLORS.get(c, "#AAB7B8") for c in cat_totals["Category"]]
            chart_total = float(cat_totals["Amount"].sum())

            fig_donut = go.Figure(go.Pie(
                labels=cat_totals["Category"],
                values=cat_totals["Amount"],
                hole=0.52,
                marker_colors=colors,
                textinfo="label+percent",
                textfont_size=11,
                hovertemplate="%{label}<br>₹%{value:,.2f}<br>%{percent}<extra></extra>",
                # legend click shows/hides slices natively
            ))
            fig_donut.update_layout(
                showlegend=True,
                legend=dict(orientation="v", x=1.02, y=0.5, font=dict(size=11)),
                margin=dict(t=20, b=20, l=10, r=120),
                height=340,
                annotations=[dict(
                    text=fmt_short(chart_total),
                    x=0.38, y=0.5,
                    font=dict(size=20, color="#333"),
                    showarrow=False,
                )],
            )
            st.plotly_chart(fig_donut, use_container_width=True)
            st.caption("💡 Click a legend item to show/hide that category.")

        # ── Budget vs Actual gauges ────────────────────────────────────────
        with right_col:
            st.markdown("#### Budget vs Actual")
            cat_spent = chart_mdf.groupby("category")["amount"].sum()

            any_row = False
            for _, brow in sel_budgets.iterrows():
                cat   = brow["category"]
                spent = float(cat_spent.get(cat, 0))
                limit = float(brow["monthly_limit"])
                if spent == 0 and limit == 0:
                    continue
                any_row = True
                pct   = min((spent / limit * 100) if limit > 0 else 0, 100)
                over  = limit > 0 and spent > limit
                color = "#FF6B6B" if over else "#4ECDC4"
                limit_txt = fmt(limit) if limit > 0 else "No limit"
                dot   = CATEGORY_COLORS.get(cat, "#AAB7B8")
                st.markdown(
                    f"""
                    <div class="bar-wrap">
                      <div class="bar-labels">
                        <span><span style="color:{dot}">●</span> <b>{cat}</b></span>
                        <span>{fmt(spent)} / {limit_txt}</span>
                      </div>
                      <div class="bar-track">
                        <div class="bar-fill" style="width:{pct}%;background:{color}"></div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            if not any_row:
                st.info("Set budgets in '🎯 Budget Settings' to see progress bars.")

    else:
        st.info(f"No expenses for {sel_month} {sel_year}. Add some with '➕ Add Expense'.")
        sel_pie_cats = []  # needed for trend chart reference below

    # ── Monthly trend bar chart ────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Monthly Trend — Last 12 Months")

    if not df.empty:
        trend_df = df[~df["category"].apply(_is_non_spend)].copy()
        trend_df["period"] = trend_df["date"].dt.to_period("M")
        end_p   = pd.Period(f"{sel_year}-{month_num:02d}", "M")
        start_p = end_p - 11
        mask    = trend_df["period"].between(start_p, end_p)
        trend_slice = trend_df[mask]

        if not trend_slice.empty:
            g = (
                trend_slice.groupby(["period", "category"])["amount"]
                .sum()
                .reset_index()
            )
            g["month_str"] = g["period"].dt.strftime("%b %Y")
            g = g.sort_values("period")

            fig_bar = px.bar(
                g,
                x="month_str", y="amount",
                color="category",
                color_discrete_map=CATEGORY_COLORS,
                barmode="stack",
                labels={"amount": "Amount (₹)", "month_str": "Month", "category": "Category"},
            )
            fig_bar.update_layout(
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(t=60, b=10),
                height=360,
                yaxis=dict(tickprefix="₹", tickformat=",.0f"),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Not enough historical data yet.")
    else:
        st.info("Add expenses to see the monthly trend chart.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE ▶ ADD EXPENSE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Add Expense":
    st.title("➕ Add New Expense")

    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        expense_date    = c1.date_input("Date", value=date.today())
        amount          = c1.number_input("Amount (₹)", min_value=0.01, step=1.0, format="%.2f")
        category        = c1.selectbox("Category", CATEGORIES)
        description     = c2.text_input("Description / Notes", placeholder="e.g. Lunch, Petrol fill, etc.")
        payment_method  = c2.selectbox("Payment Method", PAYMENT_METHODS)
        pdf_file        = c2.file_uploader("📎 Attach Receipt / Invoice (PDF)", type=["pdf"])

        submitted = st.form_submit_button("💾 Save Expense", use_container_width=True, type="primary")

        if submitted:
            if amount <= 0:
                st.error("Amount must be greater than ₹0.")
            else:
                exp_id = str(uuid.uuid4())[:8].upper()
                attachment_name = ""
                if pdf_file is not None:
                    attachment_name = save_attachment(exp_id, pdf_file.getvalue())

                df = load_expenses()
                new_row = {
                    "id":             exp_id,
                    "date":           expense_date.strftime("%Y-%m-%d"),
                    "amount":         round(amount, 2),
                    "category":       category,
                    "description":    description.strip() if description.strip() else "—",
                    "payment_method": payment_method,
                    "attachment":     attachment_name,
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_expenses(df)
                attach_note = " · 📎 receipt saved" if attachment_name else ""
                st.success(f"✅ {fmt(amount)} added under **{category}**{attach_note}.")

    # Recent entries
    st.markdown("---")
    st.markdown("#### Recent Entries (Last 15)")
    df = load_expenses()
    if not df.empty:
        recent = df.sort_values("date", ascending=False).head(15).copy()
        recent["date"]       = pd.to_datetime(recent["date"]).dt.strftime("%d %b %Y")
        recent["amount"]     = recent["amount"].apply(fmt)
        recent["receipt"]    = recent["attachment"].apply(lambda x: "📎" if x else "—")
        st.dataframe(
            recent[["date", "category", "description", "amount", "payment_method", "receipt"]].rename(
                columns={"date":"Date","category":"Category","description":"Description",
                         "amount":"Amount","payment_method":"Payment Method","receipt":"Receipt"}
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No expenses recorded yet.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE ▶ IMPORT CSV
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Import CSV":
    st.title("📂 Import from CSV")
    st.markdown(
        "Upload a bank statement or any CSV export. Map the columns, assign categories, then import."
    )

    with st.expander("📌 Tips for a smooth import"):
        st.markdown(
            """
            - Your CSV must have **at least** a **Date** and **Amount** column.
            - Amounts should be positive numbers (debits). Credit/refund rows will be skipped if negative.
            - Supported date formats: `DD/MM/YYYY`, `YYYY-MM-DD`, `DD-MMM-YYYY`, etc.
            - Most Indian bank statement exports (HDFC, ICICI, SBI, Axis) work directly.
            """
        )

    # ── Account / source name ─────────────────────────────────────────────
    acct_name = st.text_input(
        "Account Name *",
        placeholder="e.g. AU Bank Savings, HDFC Credit Card, Paytm Wallet…",
        key="import_acct_name",
        help="A label for this import batch. Used to filter and bulk-delete in Transaction History.",
    )

    uploaded = st.file_uploader("Upload file (CSV, XLSX, XLS, XLSB)", type=["csv", "xlsx", "xls", "xlsb"])

    if uploaded:
        if not acct_name.strip():
            st.warning("Please enter an Account Name above before previewing/importing.")
        else:
            try:
                ext = uploaded.name.rsplit(".", 1)[-1].lower()
                if ext == "csv":
                    raw = pd.read_csv(uploaded)
                elif ext in ("xlsx", "xls"):
                    raw = pd.read_excel(uploaded)
                elif ext == "xlsb":
                    raw = pd.read_excel(uploaded, engine="pyxlsb")
                else:
                    raw = pd.read_csv(uploaded)
                st.success(f"Loaded **{len(raw)} rows** × **{len(raw.columns)} columns**")

                with st.expander("Preview raw data (first 5 rows)"):
                    st.dataframe(raw.head(5), use_container_width=True)

                st.markdown("### Map Columns")
                opts = ["— skip —"] + list(raw.columns)

                mc1, mc2, mc3 = st.columns(3)
                col_date    = mc1.selectbox("Date column *",        opts, key="m_date")
                col_amount  = mc2.selectbox("Amount column (₹) *",  opts, key="m_amount")
                col_desc    = mc3.selectbox("Description column",   opts, key="m_desc")

                mc4, mc5 = st.columns(2)
                col_pay     = mc4.selectbox("Payment Method column (optional)", opts, key="m_pay")
                col_cat     = mc5.selectbox("Category column (optional)",       opts, key="m_cat")

                default_cat = st.selectbox("Default category for all rows", CATEGORIES, index=CATEGORIES.index("Others"))

                if st.button("🔍 Preview Import", type="secondary"):
                    if col_date == "— skip —" or col_amount == "— skip —":
                        st.error("Date and Amount columns are required.")
                    else:
                        mapped = pd.DataFrame()
                        mapped["id"]    = [str(uuid.uuid4())[:8].upper() for _ in range(len(raw))]
                        # Use format="mixed" so both native Excel dates and text strings parse correctly
                        mapped["date"]  = pd.to_datetime(
                            raw[col_date], dayfirst=True, errors="coerce", format="mixed"
                        ).dt.strftime("%Y-%m-%d")
                        mapped["amount"] = pd.to_numeric(
                            raw[col_amount].astype(str).str.replace(",","").str.replace("₹",""),
                            errors="coerce"
                        ).abs()
                        mapped["description"]    = raw[col_desc] if col_desc != "— skip —" else "Imported"
                        mapped["payment_method"] = raw[col_pay]  if col_pay  != "— skip —" else "Other"
                        mapped["category"]       = raw[col_cat]  if col_cat  != "— skip —" else default_cat
                        mapped["attachment"]     = ""
                        mapped["source"]         = acct_name.strip()

                        mapped = mapped.dropna(subset=["date", "amount"])
                        mapped = mapped[mapped["amount"] > 0]

                        if mapped.empty:
                            st.error("No valid rows found after mapping. Check your column selection.")
                        else:
                            st.session_state["csv_preview"] = mapped
                            st.success(f"**{len(mapped)} valid rows** ready to import.")
                            disp = mapped.copy()
                            disp["amount"] = disp["amount"].apply(fmt)
                            st.dataframe(
                                disp[["date","category","description","amount","payment_method"]],
                                use_container_width=True, hide_index=True,
                            )

                if st.session_state.get("csv_preview") is not None:
                    if st.button("✅ Confirm & Import", type="primary", use_container_width=True):
                        new_rows = st.session_state["csv_preview"]
                        existing = load_expenses()
                        combined = pd.concat([existing, new_rows], ignore_index=True)
                        save_expenses(combined)
                        st.session_state["csv_preview"] = None
                        st.success(f"✅ Imported **{len(new_rows)} expenses** from **{acct_name.strip()}** successfully!")
                        st.balloons()

            except Exception as exc:
                st.error(f"Error reading file: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE ▶ PDF TO CSV
# ══════════════════════════════════════════════════════════════════════════════
elif page == "PDF to CSV":
    st.title("🔄 PDF Bank Statement → CSV")
    st.markdown(
        "Upload any bank statement PDF. Transactions are **auto-detected** — "
        "no column mapping needed. Add Remarks, auto-categorize, then download "
        "your CSV or push directly into the tracker."
    )

    # ── Session state init ─────────────────────────────────────────────────
    for key in ("pdf_work", "pdf_bytes", "pdf_needs_pass", "pdf_pass_wrong"):
        if key not in st.session_state:
            st.session_state[key] = None

    # ── helper: run full extract + parse pipeline ──────────────────────────
    def _run_pipeline(file_bytes: bytes, password: str = "") -> tuple:
        # 1. Try Slice credit card parser (text-based, no tables)
        work_df, note = parse_slice_statement(file_bytes, password=password)
        if note in ("PASSWORD_REQUIRED", "WRONG_PASSWORD"):
            return None, note
        if work_df is not None:
            return work_df, note

        # 2. Try merged-cell parser (Bank of Baroda style)
        work_df, note = parse_merged_cell_statement(file_bytes, password=password)
        if note in ("PASSWORD_REQUIRED", "WRONG_PASSWORD"):
            return None, note
        if work_df is not None:
            return work_df, note

        # 3. Fall back to generic table extractor + column scorer
        raw_df, msg = extract_pdf_tables(file_bytes, password=password)
        if raw_df is None:
            return None, msg
        work_df, note = auto_parse_statement(raw_df)
        if work_df is None:
            return None, note
        return work_df, note

    # ── Step 1 · Upload ────────────────────────────────────────────────────
    st.markdown("### Step 1 — Upload PDF")
    pdf_acct_name = st.text_input(
        "Account Name *",
        placeholder="e.g. BOB Credit Card, HDFC Savings…",
        key="pdf_acct_name",
        help="A label for this import batch. Used to filter and bulk-delete in Transaction History.",
    )
    pdf_upload = st.file_uploader(
        "Upload bank statement PDF", type=["pdf"], key="pdf_uploader"
    )

    if pdf_upload:
        file_bytes = pdf_upload.getvalue()
        if file_bytes != st.session_state.get("pdf_bytes"):
            st.session_state["pdf_bytes"]      = file_bytes
            st.session_state["pdf_work"]       = None
            st.session_state["pdf_needs_pass"] = False
            st.session_state["pdf_pass_wrong"] = False

            with st.spinner("Extracting and parsing transactions…"):
                work_df, msg = _run_pipeline(file_bytes)

            if msg == "PASSWORD_REQUIRED":
                st.session_state["pdf_needs_pass"] = True
            elif work_df is None:
                st.error(msg)
            else:
                st.session_state["pdf_work"] = work_df
                st.success(f"✅ Auto-parsed: {msg}")

    # ── Password prompt ────────────────────────────────────────────────────
    if st.session_state.get("pdf_needs_pass") and st.session_state["pdf_work"] is None:
        st.warning("🔒 This PDF is password-protected. Enter the password to unlock it.")
        if st.session_state.get("pdf_pass_wrong"):
            st.error("❌ Incorrect password — please try again.")

        with st.form("pdf_pass_form"):
            entered_pass = st.text_input(
                "PDF Password", type="password",
                placeholder="Enter the PDF password…",
                help="Used only to unlock this file — never stored.",
            )
            if st.form_submit_button("🔓 Unlock & Extract", type="primary"):
                if not entered_pass:
                    st.warning("Please enter a password.")
                else:
                    with st.spinner("Unlocking and parsing…"):
                        work_df, msg = _run_pipeline(
                            st.session_state["pdf_bytes"], password=entered_pass
                        )
                    if msg == "WRONG_PASSWORD":
                        st.session_state["pdf_pass_wrong"] = True
                        st.rerun()
                    elif work_df is None:
                        st.error(msg)
                    else:
                        st.session_state["pdf_work"]       = work_df
                        st.session_state["pdf_needs_pass"] = False
                        st.session_state["pdf_pass_wrong"] = False
                        st.success(f"✅ Unlocked and parsed: {msg}")
                        st.rerun()

    # ── Step 2 · Review, Remarks & Categorise ─────────────────────────────
    if st.session_state["pdf_work"] is not None:
        work_df = st.session_state["pdf_work"]

        st.markdown("### Step 2 — Review, Add Remarks & Categorize")
        st.caption(
            "Columns **Date, Amount, Description, Type** are auto-detected from your PDF. "
            "Fill in **Remarks** per row, then click **Auto-Categorize** to set categories. "
            "Override any Category cell with the dropdown."
        )

        # KPI strip
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Transactions", len(work_df))
        k2.metric("Total Debits",  fmt(float(work_df.loc[work_df["Type"]=="Debit",  "Amount"].sum())))
        k3.metric("Total Credits", fmt(float(work_df.loc[work_df["Type"]=="Credit", "Amount"].sum())))
        filled = int((work_df["Remarks"].str.strip() != "").sum())
        k4.metric("Remarks Filled", f"{filled} / {len(work_df)}")

        st.markdown("")

        edited_df = st.data_editor(
            work_df,
            key="pdf_editor",
            use_container_width=True,
            num_rows="fixed",
            column_config={
                "Date":           st.column_config.TextColumn("Date", disabled=True, width="small"),
                "Amount":         st.column_config.NumberColumn("Amount (₹)", format="₹%.2f", disabled=True, width="small"),
                "Type":           st.column_config.TextColumn("Type", disabled=True, width="small"),
                "Description":    st.column_config.TextColumn("Description", disabled=True, width="large"),
                "Remarks":        st.column_config.TextColumn(
                    "Remarks ✏️", width="medium",
                    help="e.g. 'Zomato', 'Petrol', 'Electricity bill' — drives auto-categorization",
                ),
                "Category":       st.column_config.SelectboxColumn(
                    "Category", options=CATEGORIES, width="medium",
                    help="Auto-filled from Remarks; override freely",
                ),
                "Payment Method": st.column_config.SelectboxColumn(
                    "Payment Method", options=PAYMENT_METHODS, width="small",
                ),
            },
            hide_index=True,
            height=460,
        )

        # Action bar
        ab1, ab2, ab3 = st.columns([3, 3, 4])

        if ab1.button("🤖 Auto-Categorize from Remarks", type="primary", use_container_width=True):
            updated = edited_df.copy()
            updated["Category"] = updated["Remarks"].apply(detect_category)
            changed = int((updated["Category"] != edited_df["Category"]).sum())
            st.session_state["pdf_work"] = updated
            st.toast(f"Filled {changed} categories from Remarks.", icon="🤖")
            st.rerun()

        if ab2.button("💾 Save Edits", type="secondary", use_container_width=True):
            st.session_state["pdf_work"] = edited_df.copy()
            st.toast("Edits saved.", icon="💾")
            st.rerun()

        if ab3.button("🔄 Re-upload / Reset", type="secondary", use_container_width=True):
            for k in ("pdf_work","pdf_bytes","pdf_needs_pass","pdf_pass_wrong"):
                st.session_state[k] = None
            st.rerun()

        st.markdown("---")

        # Summary
        final_df = st.session_state["pdf_work"]
        st.markdown("#### Summary")
        s1, s2, s3 = st.columns(3)
        s1.metric("Total Rows",       len(final_df))
        s2.metric("Total Amount",     fmt(float(final_df["Amount"].sum())))
        s3.metric("Categories Used",  final_df["Category"].nunique())

        with st.expander("Category breakdown"):
            for cat, grp in final_df.groupby("Category"):
                st.markdown(f"- **{cat}**: {len(grp)} rows · {fmt(float(grp['Amount'].sum()))}")

        st.markdown("---")
        st.markdown("### Step 3 — Export")

        ex1, ex2, ex3 = st.columns([2, 2, 4])

        export_df = final_df[["Date","Description","Amount","Type","Category","Remarks","Payment Method"]].copy()
        pdf_fmt = ex1.selectbox("Export format", EXPORT_FORMATS, key="pdf_export_fmt")
        pdf_data, pdf_mime, pdf_ext, pdf_warn = export_df_bytes(export_df, pdf_fmt)
        if pdf_warn:
            st.warning(pdf_warn)
        ex2.download_button(
            f"📥 Download {pdf_fmt}",
            data=pdf_data,
            file_name=f"statement_{datetime.now().strftime('%Y%m%d_%H%M')}.{pdf_ext}",
            mime=pdf_mime,
            use_container_width=True,
            type="primary",
        )

        with ex3:
            if st.button("➕ Import into Expense Tracker", use_container_width=True, type="secondary"):
                existing = load_expenses()
                _pdf_src = st.session_state.get("pdf_acct_name", "").strip() or "PDF Import"
                rows = []
                for _, row in final_df.iterrows():
                    desc = str(row["Description"]).strip()
                    rmk  = str(row["Remarks"]).strip()
                    rows.append({
                        "id":             str(uuid.uuid4())[:8].upper(),
                        "date":           row["Date"],
                        "amount":         round(float(row["Amount"]), 2),
                        "category":       row["Category"],
                        "description":    f"{desc} [{rmk}]".strip(" []") if rmk else desc,
                        "payment_method": row["Payment Method"],
                        "attachment":     "",
                        "source":         _pdf_src,
                    })
                combined = pd.concat([existing, pd.DataFrame(rows)], ignore_index=True)
                save_expenses(combined)
                st.success(f"✅ Imported **{len(rows)} transactions** from **{_pdf_src}** into your tracker!")
                st.balloons()
                for k in ("pdf_work","pdf_bytes","pdf_needs_pass","pdf_pass_wrong"):
                    st.session_state[k] = None


# ══════════════════════════════════════════════════════════════════════════════
# PAGE ▶ BUDGET SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Budget Settings":
    st.title("🎯 Monthly Budget Settings")
    st.markdown("Set a monthly spending cap per category. Leave at **₹0** for no limit.")

    budgets = load_budgets()

    with st.form("budget_form"):
        st.markdown("### Set Limits")
        inputs: dict = {}
        cols = st.columns(2)
        for i, cat in enumerate(CATEGORIES):
            current = float(
                budgets.loc[budgets["category"] == cat, "monthly_limit"].values[0]
                if cat in budgets["category"].values else 0.0
            )
            dot = CATEGORY_COLORS.get(cat, "#AAB7B8")
            col = cols[i % 2]
            col.markdown(f'<span style="color:{dot};font-size:18px">●</span> **{cat}**', unsafe_allow_html=True)
            inputs[cat] = col.number_input(
                cat, min_value=0.0, value=current,
                step=500.0, format="%.0f",
                key=f"b_{cat}", label_visibility="collapsed",
            )

        if st.form_submit_button("💾 Save Budgets", use_container_width=True, type="primary"):
            new_bdf = pd.DataFrame({
                "category":     list(inputs.keys()),
                "monthly_limit": list(inputs.values()),
            })
            save_budgets(new_bdf)
            st.success("✅ Budgets saved!")
            st.rerun()

    st.markdown("---")
    st.markdown("#### Current Budget Summary")
    budgets = load_budgets()
    active  = budgets[budgets["monthly_limit"] > 0].copy()
    if not active.empty:
        active["Limit"] = active["monthly_limit"].apply(fmt)
        st.dataframe(
            active[["category", "Limit"]].rename(columns={"category": "Category"}),
            use_container_width=True, hide_index=True,
        )
        st.metric("Total Monthly Budget", fmt(float(active["monthly_limit"].sum())))
    else:
        st.info("No budgets configured yet.")

    # ── Category Mapping Master ────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🗂️ Category Mapping Master")
    st.caption(
        "Add your own keyword → category rules. Your rules are checked **first** — "
        "they override the built-in list. Keywords are case-insensitive and matched as a substring."
    )

    custom_kw = load_custom_keywords()

    # ── Download blank template ────────────────────────────────────────────
    template_csv = "keyword,category\nZomato,Food\nIRCTC,Trip\n"
    st.download_button(
        "📥 Download Template (CSV)",
        data=template_csv.encode("utf-8"),
        file_name="category_mapping_template.csv",
        mime="text/csv",
    )

    # ── Upload filled template ─────────────────────────────────────────────
    up_map = st.file_uploader(
        "Upload filled mapping CSV (keyword, category columns)",
        type=["csv", "xlsx", "xls"],
        key="kw_upload",
    )
    if up_map:
        try:
            ext = up_map.name.rsplit(".", 1)[-1].lower()
            up_df = pd.read_csv(up_map) if ext == "csv" else pd.read_excel(up_map)
            # Normalise column names to lowercase
            up_df.columns = [c.strip().lower() for c in up_df.columns]
            if "keyword" not in up_df.columns or "category" not in up_df.columns:
                st.error("File must have 'keyword' and 'category' columns.")
            else:
                up_df = up_df[["keyword", "category"]].dropna()
                up_df["keyword"]  = up_df["keyword"].astype(str).str.strip().str.lower()
                up_df["category"] = up_df["category"].astype(str).str.strip()
                # Keep only valid categories
                invalid = up_df[~up_df["category"].isin(CATEGORIES)]
                up_df   = up_df[up_df["category"].isin(CATEGORIES)]
                if not invalid.empty:
                    st.warning(
                        f"{len(invalid)} row(s) skipped — unknown category: "
                        + ", ".join(invalid["category"].unique().tolist())
                    )
                if not up_df.empty:
                    merged = pd.concat([custom_kw, up_df], ignore_index=True)
                    merged = merged.drop_duplicates(subset=["keyword"], keep="last")
                    save_custom_keywords(merged)
                    st.success(f"✅ Added / updated {len(up_df)} mapping(s).")
                    st.rerun()
        except Exception as exc:
            st.error(f"Could not read file: {exc}")

    # ── Current custom mappings table ─────────────────────────────────────
    st.markdown("#### Current Custom Mappings")
    custom_kw = load_custom_keywords()
    if custom_kw.empty:
        st.info("No custom mappings yet. Upload a CSV above to add some.")
    else:
        st.caption(f"{len(custom_kw)} custom rule(s) active.")
        disp_kw = custom_kw.copy().reset_index(drop=True)
        disp_kw.insert(0, "Delete", False)
        edited_kw = st.data_editor(
            disp_kw,
            key="kw_editor",
            use_container_width=True,
            hide_index=True,
            column_config={
                "Delete":   st.column_config.CheckboxColumn("🗑️", width="small"),
                "keyword":  st.column_config.TextColumn("Keyword",  width="medium", disabled=True),
                "category": st.column_config.SelectboxColumn(
                    "Category", options=CATEGORIES, width="medium"
                ),
            },
        )
        to_delete = edited_kw[edited_kw["Delete"] == True].index.tolist()
        # Apply category edits first, then handle deletions
        updated_cats = edited_kw[~edited_kw["Delete"]].drop(columns=["Delete"]).reset_index(drop=True)
        if to_delete:
            if st.button(f"🗑️ Delete {len(to_delete)} selected mapping(s)", type="primary"):
                save_custom_keywords(updated_cats)
                st.success(f"Deleted {len(to_delete)} mapping(s).")
                st.rerun()
        if st.button("💾 Save Category Edits", type="secondary"):
            save_custom_keywords(updated_cats)
            st.success("Mappings saved.")
            st.rerun()

        # Export current mappings
        kw_csv = custom_kw.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Export Current Mappings",
            data=kw_csv,
            file_name="my_category_mappings.csv",
            mime="text/csv",
        )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE ▶ TRANSACTION HISTORY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Transaction History":
    st.title("📋 Transaction History")

    df = load_expenses()

    if df.empty:
        st.info("No transactions yet. Add expenses via '➕ Add Expense'.")
    else:
        # ── Filters ────────────────────────────────────────────────────────
        f1, f2, f3, f4 = st.columns(4)

        periods       = sorted(df["date"].dt.to_period("M").unique(), reverse=True)
        period_opts   = ["All"] + [str(p) for p in periods]
        sel_period    = f1.selectbox("Month", period_opts, key="hist_period")

        cat_opts      = ["All"] + CATEGORIES
        sel_cat       = f2.selectbox("Category", cat_opts, key="hist_cat")

        pm_opts       = ["All"] + PAYMENT_METHODS
        sel_pm        = f3.selectbox("Payment", pm_opts, key="hist_pm")

        search        = f4.text_input("Search description", placeholder="Type to filter…")

        # Source / account filter
        source_vals   = sorted(df["source"].dropna().unique().tolist()) if "source" in df.columns else []
        source_vals   = [s for s in source_vals if s]
        source_opts   = ["All"] + source_vals
        sel_source    = st.selectbox(
            "Filter by Account / Import Source",
            source_opts,
            key="hist_source",
            help="Filter transactions by the account name used when importing",
        ) if source_vals else "All"

        filtered = df.copy()
        if sel_period != "All":
            filtered = filtered[filtered["date"].dt.to_period("M").astype(str) == sel_period]
        if sel_cat != "All":
            filtered = filtered[filtered["category"] == sel_cat]
        if sel_pm != "All":
            filtered = filtered[filtered["payment_method"] == sel_pm]
        if sel_source != "All":
            filtered = filtered[filtered["source"].astype(str) == sel_source]
        if search:
            filtered = filtered[filtered["description"].str.contains(search, case=False, na=False)]

        filtered = filtered.sort_values("date", ascending=False)

        # ── Summary row ────────────────────────────────────────────────────
        s1, s2, s3 = st.columns(3)
        s1.metric("Matching Transactions", len(filtered))
        s2.metric("Total Amount",          fmt(float(filtered["amount"].sum())))
        s3.metric("Avg per Transaction",
                  fmt(float(filtered["amount"].mean())) if not filtered.empty else "—")

        st.markdown("---")

        # ── Selectable table ───────────────────────────────────────────────
        st.caption("✅ Tick the checkbox on any row to select it, then click **Delete Selected**.")

        disp = filtered.copy()
        disp["_date"]    = pd.to_datetime(disp["date"]).dt.strftime("%d %b %Y")
        disp["_amount"]  = disp["amount"].apply(fmt)
        disp["_receipt"] = disp["attachment"].apply(lambda x: "📎" if x else "—")
        disp["_source"]  = disp["source"].fillna("").apply(lambda x: x if x else "—")
        disp["Select"]   = False

        edited = st.data_editor(
            disp[["Select","id","_date","category","description","_amount","payment_method","_source","_receipt"]].rename(
                columns={
                    "id":"ID","_date":"Date","category":"Category",
                    "description":"Description","_amount":"Amount",
                    "payment_method":"Payment","_source":"Account","_receipt":"Receipt",
                }
            ),
            key="hist_editor",
            use_container_width=True,
            hide_index=True,
            height=420,
            column_config={
                "Select":      st.column_config.CheckboxColumn("✓", width="small"),
                "ID":          st.column_config.TextColumn("ID",          disabled=True, width="small"),
                "Date":        st.column_config.TextColumn("Date",        disabled=True, width="small"),
                "Category":    st.column_config.TextColumn("Category",    disabled=True, width="small"),
                "Description": st.column_config.TextColumn("Description", disabled=True, width="large"),
                "Amount":      st.column_config.TextColumn("Amount",      disabled=True, width="small"),
                "Payment":     st.column_config.TextColumn("Payment",     disabled=True, width="small"),
                "Account":     st.column_config.TextColumn("Account",     disabled=True, width="medium"),
                "Receipt":     st.column_config.TextColumn("Receipt",     disabled=True, width="small"),
            },
        )

        selected_ids = edited[edited["Select"] == True]["ID"].tolist()

        # Action bar below table
        ab1, ab2, ab3 = st.columns([3, 3, 4])

        if selected_ids:
            n_sel = len(selected_ids)
            if ab1.button(f"🗑️ Delete {n_sel} selected", type="primary", use_container_width=True):
                for sid in selected_ids:
                    match = df[df["id"] == sid]
                    if not match.empty:
                        delete_attachment(str(match.iloc[0].get("attachment", "")))
                df_new = df[~df["id"].isin(selected_ids)]
                save_expenses(df_new)
                st.success(f"Deleted {n_sel} transaction(s).")
                st.rerun()
        else:
            ab1.button("🗑️ Delete Selected", disabled=True, use_container_width=True,
                       help="Tick checkboxes in the table above to select transactions")

        hist_fmt = ab2.selectbox(
            "Format", EXPORT_FORMATS, key="hist_export_fmt", label_visibility="collapsed"
        )
        exp_data, exp_mime, exp_ext, exp_warn = export_df_bytes(
            filtered.drop(columns=["attachment"], errors="ignore"), hist_fmt
        )
        if exp_warn:
            st.warning(exp_warn)
        ab3.download_button(
            f"📥 Export as {hist_fmt}",
            data=exp_data,
            file_name=f"expenses_{datetime.now().strftime('%Y%m%d_%H%M')}.{exp_ext}",
            mime=exp_mime,
            use_container_width=True,
        )

        # ── Batch delete by account ────────────────────────────────────────
        if source_vals:
            st.markdown("---")
            st.markdown("### 🗂️ Delete Import Batch by Account")
            st.caption(
                "Remove all transactions that were imported under a specific account name. "
                "Use this to undo a duplicate or wrong import."
            )
            bd1, bd2 = st.columns([3, 2])
            batch_acct = bd1.selectbox(
                "Select account batch to delete",
                source_vals,
                key="batch_del_acct",
                label_visibility="collapsed",
            )
            batch_rows = df[df["source"].astype(str) == batch_acct]
            bd1.caption(f"{len(batch_rows)} transaction(s) tagged under **{batch_acct}**")
            if bd2.button(
                f"🗑️ Delete all {len(batch_rows)} rows from '{batch_acct}'",
                type="primary",
                use_container_width=True,
                key="batch_del_btn",
            ):
                for _, row in batch_rows.iterrows():
                    delete_attachment(str(row.get("attachment", "")))
                df_new = df[df["source"].astype(str) != batch_acct]
                save_expenses(df_new)
                st.success(f"✅ Deleted {len(batch_rows)} transactions from **{batch_acct}**.")
                st.rerun()

        # ── Attachment Manager ─────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 📎 Attachment Manager")
        st.caption("View, download, or delete PDF receipts linked to a transaction.")

        # Show only transactions that have attachments in filtered view
        with_attach = filtered[filtered["attachment"].str.len() > 0].copy()
        no_attach   = filtered[filtered["attachment"].str.len() == 0]

        if not with_attach.empty:
            st.markdown(
                f"**{len(with_attach)}** transaction(s) in current view have a PDF receipt attached."
            )

        att_id_input = st.text_input(
            "Enter Transaction ID to manage attachment",
            placeholder="e.g. A3F9C2B1",
            key="att_id",
        )

        if att_id_input:
            clean_att_id = att_id_input.strip().upper()
            row_match    = df[df["id"] == clean_att_id]

            if row_match.empty:
                st.error(f"Transaction ID '{clean_att_id}' not found.")
            else:
                row = row_match.iloc[0]
                st.markdown(
                    f"**{row['category']}** · {row['description']} · "
                    f"{fmt(float(row['amount']))} · "
                    f"{pd.to_datetime(row['date']).strftime('%d %b %Y')}"
                )

                current_att = str(row.get("attachment", ""))

                if current_att:
                    pdf_bytes = read_attachment(current_att)
                    att_col1, att_col2, att_col3 = st.columns([2, 2, 4])

                    if pdf_bytes:
                        att_col1.download_button(
                            "⬇️ Download PDF",
                            data=pdf_bytes,
                            file_name=current_att,
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    else:
                        att_col1.warning("PDF file missing on disk.")

                    if att_col2.button("🗑️ Delete PDF", type="secondary", use_container_width=True):
                        delete_attachment(current_att)
                        df.loc[df["id"] == clean_att_id, "attachment"] = ""
                        save_expenses(df)
                        st.success(f"PDF receipt deleted for transaction {clean_att_id}.")
                        st.rerun()
                else:
                    # No attachment yet — allow uploading one
                    st.info("No PDF receipt attached to this transaction.")
                    new_pdf = st.file_uploader(
                        "Attach a PDF receipt now", type=["pdf"], key=f"attach_upload_{clean_att_id}"
                    )
                    if new_pdf is not None:
                        if st.button("💾 Save PDF", type="primary"):
                            fname = save_attachment(clean_att_id, new_pdf.getvalue())
                            df.loc[df["id"] == clean_att_id, "attachment"] = fname
                            save_expenses(df)
                            st.success(f"PDF receipt saved for transaction {clean_att_id}.")
                            st.rerun()
