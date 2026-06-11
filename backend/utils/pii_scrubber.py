import re

REDACTED = "[REDACTED]"

# Credit card numbers: 13-19 digits, allowing spaces/dashes between groups
CC_PATTERN = re.compile(
    r"\b(?:\d[ \d-]*\d)\b",
)

# Phone numbers: US formats like (123) 456-7890, 123-456-7890, +1 123 456 7890, etc.
PHONE_PATTERN = re.compile(
    r"(?:\+?1[\s.-]?)?"  # optional country code
    r"(?:"
    r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}"  # US: (123)456-7890, 123-456-7890
    r"|"
    r"\+\d{1,3}[\s.-]\d{1,4}[\s.-]\d{1,4}[\s.-]\d{1,9}"  # International: +44 20 7946 0958
    r")"
)

# Email addresses: standard email format
EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
)

PATTERNS: list[re.Pattern[str]] = [CC_PATTERN, PHONE_PATTERN, EMAIL_PATTERN]


def _is_credit_card_match(text: str) -> bool:
    digits_only = re.sub(r"[^\d]", "", text)
    length = len(digits_only)
    return 13 <= length <= 19


def scrub_pii(text: str) -> str:
    result = text

    # Credit cards — validate digit count before redacting
    for match in CC_PATTERN.finditer(text):
        candidate = match.group()
        if _is_credit_card_match(candidate):
            result = result.replace(candidate, REDACTED, 1)

    # Phone numbers
    result = PHONE_PATTERN.sub(REDACTED, result)

    # Email addresses
    result = EMAIL_PATTERN.sub(REDACTED, result)

    return result