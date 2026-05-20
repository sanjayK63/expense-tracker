"""
Shared categorizer — single source of truth for keyword → category mapping.
Used by PDF parser, CSV import, and WhatsApp bot.
"""

KEYWORD_MAP: dict[str, list[str]] = {
    "Food": [
        "zomato","swiggy","food","restaurant","cafe","coffee","lunch","dinner",
        "breakfast","grocery","supermarket","superm","blinkit","bigbasket","zepto",
        "dunzo","dominos","pizza","burger","kfc","mcdonald","subway","dhaba","canteen",
        "mess","tiffin","bakery","bake","juice","snack","spicy","tandoor","udupi",
        "confecti","grand store","family super","n fresh","fresh s",
    ],
    "Transport": [
        "uber","ola","rapido","petrol","fuel","diesel","metro","auto",
        "taxi","cab","toll","fastag","parking","rickshaw","bmtc","dtc",
    ],
    "Utilities": [
        "electricity","internet","broadband","recharge","jio","airtel","vodafone",
        "bsnl","water bill","gas bill","lpg","cylinder","maintenance","rent","emi",
        "bescom","msedcl","tata power","tangedco","tneb","kseb",
    ],
    "Shopping & Health": [
        "amazon","flipkart","myntra","meesho","ajio","nykaa","firstcry",
        "pharmacy","medical","hospital","doctor","clinic","medicine","chemist",
        "health","gym","fitness","yoga","salon","spa","barber","apollo","medplus",
        "netmeds","1mg","mr diy","dmart","reliance retail",
    ],
    "Entertainment & Education": [
        "netflix","prime video","hotstar","disney","spotify","youtube premium",
        "movie","cinema","pvr","inox","bookmyshow","udemy","coursera","unacademy",
        "byju","books","kindle","gaming","ca monk","benchmarx","academy","coaching",
        "icai","tuition",
    ],
    "Investments & Savings": [
        "sip","mutual fund"," mf ","stock","equity","zerodha","groww","upstox",
        "fixed deposit"," fd "," rd ","ppf","nps","insurance","lic","investment",
    ],
    "Contra": [
        "contra","self transfer","own account","neft","rtgs","imps",
        "repayment","credit card repayment","transfer","wallet transfer","cashback",
        "slice","bob card",
    ],
    "Trip": [
        "oyo","makemytrip","cleartrip","goibibo","holiday","resort","airbnb",
        "irctc","indian railway","redbus","ksrtc","gsrtc","apsrtc","state transport",
        "karnatakasta","kerala state","flight","airline","indigo","spicejet",
        "air india","vistara","akasa","airport",
    ],
    "Travel to Chennai": [
        "tnstc","zingbus","abhibus",
    ],
}

CATEGORIES_LOWER = [c.lower() for c in KEYWORD_MAP]


def detect_category(remark: str, custom_rules: list[dict] | None = None) -> str:
    if not remark or not str(remark).strip():
        return "Others"
    r = str(remark).lower()
    # Custom rules win
    if custom_rules:
        for rule in custom_rules:
            kw  = str(rule.get("keyword", "")).strip().lower()
            cat = str(rule.get("category", "")).strip()
            if kw and cat and kw in r:
                return cat
    # Built-in rules
    for cat, keywords in KEYWORD_MAP.items():
        if any(kw in r for kw in keywords):
            return cat
    return "Others"
