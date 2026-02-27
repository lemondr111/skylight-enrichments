#!/usr/bin/env python3
"""
build.py — Compile links/*.yaml → links.json

Usage:
    python build.py            # validates + writes links.json
    python build.py --check    # validate only, no output written (used by CI)

Exit codes:
    0  success
    1  validation error(s) found
"""
import sys
import json
import re
import argparse
from datetime import date, timezone
from pathlib import Path
from urllib.parse import urlparse

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: pip install pyyaml")

# ── Constants ──────────────────────────────────────────────────────────────────

LINKS_DIR = Path(__file__).parent / "links"
OUT_FILE  = Path(__file__).parent / "links.json"

# Filename stem → display category name
FILENAME_TO_CATEGORY = {
    "archives-press":       "Archives & Press",
    "environment-science":  "Environment & Science",
    "government-legal":     "Government & Legal",
    "hash-cracking":        "Hash Cracking",
    "historical":           "Historical",
    "maps":                 "Maps",
    "network-scanning":     "Network Scanning",
    "people-search":        "People Search",
    "search-files":         "Search & Files",
    "social-video":         "Social & Video",
    "social-profiles":      "Social Profiles",
    "threat-intelligence":  "Threat Intelligence",
    "username-search":      "Username Search",
    "validation-tools":     "Validation & Tools",
    "vehicle-lookup":       "Vehicle Lookup",
    "whois-dns":            "WHOIS & DNS",
}

# All input types recognised by Skylight
KNOWN_TYPES = {
    "name", "alias", "domain", "email-address", "ip-address", "IPV6",
    "phone-number", "hashtag", "url", "gps-coordinates", "crypto-address",
    "VIN", "hash", "any",
}

KNOWN_PAYWALLS = {"Free", "Freemium", "Paid"}

# URL template placeholders: {value}, {value:formatter}, {value|formatter}
PLACEHOLDER_RE = re.compile(r"\{(\w+)(?:[|:](\w+))?\}")

KNOWN_FORMATTERS = {
    "urlEncode", "base64", "lower", "upper",
    "stripPunct", "spaceToNothing", "spaceToDash", "spaceToDot",
    "userFromEmail", "domainFromEmail", "firstName", "lastName",
    "noEncoding", "firstIP",
}

# ── Validation ─────────────────────────────────────────────────────────────────

def validate_entry(entry: dict, source: str) -> list[str]:
    """Return a list of error strings (empty = valid)."""
    errors = []
    eid = entry.get("id", "?")
    loc = f"{source} id={eid}"

    for field in ("id", "display", "url", "types"):
        if not entry.get(field):
            errors.append(f"{loc}: missing required field '{field}'")

    if not isinstance(entry.get("types"), list) or len(entry["types"]) == 0:
        errors.append(f"{loc}: 'types' must be a non-empty list")
    else:
        for t in entry["types"]:
            if t not in KNOWN_TYPES:
                errors.append(f"{loc}: unknown type '{t}' — add it to KNOWN_TYPES in build.py if intentional")

    pw = entry.get("payWall", "Free")
    if pw not in KNOWN_PAYWALLS:
        errors.append(f"{loc}: payWall must be one of {KNOWN_PAYWALLS}, got '{pw}'")

    url = entry.get("url", "")
    for _, fmt in PLACEHOLDER_RE.findall(url):
        if fmt and fmt not in KNOWN_FORMATTERS:
            errors.append(f"{loc}: unknown formatter '{fmt}' in URL — add it to KNOWN_FORMATTERS in build.py if intentional")

    return errors

# ── Build ──────────────────────────────────────────────────────────────────────

def favicon_url(url: str) -> str:
    """Derive a Google S2 favicon URL from a link URL."""
    try:
        host = urlparse(url).hostname or ""
        return f"https://www.google.com/s2/favicons?domain={host}&sz=32"
    except Exception:
        return ""


def build(check_only: bool = False) -> int:
    errors: list[str] = []
    links: list[dict] = []
    seen_ids: set[str] = set()

    yaml_files = sorted(LINKS_DIR.glob("*.yaml"))
    if not yaml_files:
        print(f"ERROR: no YAML files found in {LINKS_DIR}", file=sys.stderr)
        return 1

    for yaml_file in yaml_files:
        stem = yaml_file.stem
        category = FILENAME_TO_CATEGORY.get(stem)
        if category is None:
            print(f"WARNING: '{yaml_file.name}' has no category mapping in FILENAME_TO_CATEGORY — skipping", file=sys.stderr)
            continue

        with yaml_file.open(encoding="utf-8") as f:
            try:
                entries = yaml.safe_load(f)
            except yaml.YAMLError as exc:
                errors.append(f"{yaml_file.name}: YAML parse error — {exc}")
                continue

        if not isinstance(entries, list):
            errors.append(f"{yaml_file.name}: expected a YAML list at the top level")
            continue

        file_errors = []
        for entry in entries:
            if not isinstance(entry, dict):
                file_errors.append(f"{yaml_file.name}: each entry must be a mapping (dict)")
                continue

            eid = str(entry.get("id", ""))

            # Duplicate ID check
            if eid in seen_ids:
                file_errors.append(f"{yaml_file.name} id={eid}: duplicate ID — each link must have a unique id")
            seen_ids.add(eid)

            # Field-level validation
            file_errors.extend(validate_entry(entry, yaml_file.name))

            # Build the final output object (fill in defaults, clean up)
            url = str(entry.get("url", "")).strip()  # strip stray whitespace/tabs

            link = {
                "id":          eid,
                "provider":    str(entry.get("provider", "")),
                "display":     str(entry.get("display", "")),
                "icon":        entry.get("icon") or favicon_url(url),
                "description": str(entry.get("description", "")),
                "region":      str(entry.get("region", "Global")),
                "payWall":     str(entry.get("payWall", "Free")),
                "url":         url,
                "category":    category,
                "priority":    int(entry.get("priority", 0)),
                "types":       list(entry.get("types", [])),
                "autorun":     bool(entry.get("autorun", False)),
            }
            links.append(link)

        errors.extend(file_errors)
        status = "ERROR" if file_errors else "OK"
        print(f"  [{status:5s}]  {yaml_file.name}  ({len(entries)} links)")

    print()

    if errors:
        print(f"{'─'*60}")
        print(f"VALIDATION FAILED — {len(errors)} error(s):\n")
        for e in errors:
            print(f"  ✗  {e}")
        print(f"{'─'*60}")
        return 1

    if check_only:
        print(f"Validation passed — {len(links)} links, no errors.")
        return 0

    output = {
        "_note":     "DO NOT EDIT — generated by build.py from links/*.yaml. Edit the YAML files instead.",
        "version":   "1.0.0",
        "updatedAt": date.today().isoformat(),
        "links":     links,
    }

    with OUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"✓  Wrote {OUT_FILE.name}  ({len(links)} links)")
    return 0


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build links.json from links/*.yaml")
    parser.add_argument("--check", action="store_true", help="Validate only, do not write output")
    args = parser.parse_args()
    sys.exit(build(check_only=args.check))
