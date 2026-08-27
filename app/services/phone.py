import re


ALGERIA_MOBILE_RE = re.compile(r"^\+213[567]\d{8}$")


def normalize_algerian_phone(value: str) -> str:
    raw = (value or "").strip()
    digits = re.sub(r"\D+", "", raw)
    if digits.startswith("00213"):
        digits = digits[2:]
    if digits.startswith("213"):
        normalized = "+" + digits
    elif digits.startswith("0") and len(digits) == 10:
        normalized = "+213" + digits[1:]
    elif len(digits) == 9 and digits[0] in "567":
        normalized = "+213" + digits
    else:
        normalized = "+" + digits if digits else ""
    return normalized


def is_valid_algerian_phone(value: str) -> bool:
    return bool(ALGERIA_MOBILE_RE.match(normalize_algerian_phone(value)))


def mask_phone(value: str) -> str:
    normalized = normalize_algerian_phone(value)
    if len(normalized) < 8:
        return "***"
    return f"{normalized[:4]}***{normalized[-3:]}"
