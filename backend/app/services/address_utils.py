"""
Address normalization and matching utilities.

Shared between routes/reports.py (nearby API) and routes/cron.py (alert matching)
so both use the same fuzzy-match logic for street type abbreviations.
"""


def normalize_addr(a: str) -> str:
    """
    Normalize street-type abbreviations for address fuzzy matching.
    Covers 13 common street types, applied symmetrically to both query and ticket address.
    Defined at module level so it's compiled once at import time (not per-request).

    Examples:
        "580 California Street, San Francisco, CA" → "580 california st san francisco ca"
        "580 California St"                         → "580 california st"
    """
    a = a.lower().strip()
    # Remove punctuation
    a = a.replace(".", "").replace(",", "")
    # Full → abbreviated (longer strings first to avoid partial matches)
    replacements = [
        (" boulevard", " blvd"),
        (" terrace", " ter"),
        (" avenue", " ave"),
        (" street", " st"),
        (" drive", " dr"),
        (" court", " ct"),
        (" place", " pl"),
        (" lane", " ln"),
        (" road", " rd"),
        (" circle", " cir"),
        (" highway", " hwy"),
        (" parkway", " pkwy"),
        (" square", " sq"),
    ]
    for full, abbr in replacements:
        a = a.replace(full, abbr)
    return a


def addresses_match(addr1: str, addr2: str) -> bool:
    """
    Fuzzy address match: returns True if one address is a substring of the other
    after normalization.

    This handles common mismatches like:
        "580 California St"  vs  "580 California St, San Francisco, CA 94104"
        "61 Chattanooga Street" vs "61 Chattanooga St"
        "Intersection Annie St, Stevenson St" (excluded — no street number, won't match)

    Also applies street-number-only logic: if one address starts with a digit,
    verify the street number matches before doing the substring check.
    """
    n1 = normalize_addr(addr1)
    n2 = normalize_addr(addr2)

    # Fast path: direct substring match
    if n1 in n2 or n2 in n1:
        return True

    # Street-number check: if either address starts with a number, make sure
    # the number matches before declaring a substring hit.
    parts1 = n1.split()
    parts2 = n2.split()
    if parts1 and parts2 and parts1[0].isdigit() and parts2[0].isdigit():
        if parts1[0] != parts2[0]:
            return False  # Different street number — definitely not a match
        # Same number; check street name substring
        street1 = " ".join(parts1[1:])
        street2 = " ".join(parts2[1:])
        return street1 in street2 or street2 in street1

    return False
