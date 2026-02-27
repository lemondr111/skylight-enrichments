# Contributing to skylight-enrichments

This repo hosts the link and widget definitions used by Skylight.
The source of truth is the YAML files in `links/`. The `links.json` file is
**generated automatically** — do not edit it by hand.

---

## How to add or edit a link

1. Open the relevant file in `links/` — each file is one category.
2. Add or modify a YAML entry.
3. Run `python build.py` locally to validate and regenerate `links.json`.
4. Commit both the YAML change and the updated `links.json`.

When you push to `main`, GitHub Actions will re-validate and regenerate
`links.json` automatically, so step 3 is optional if you prefer to let CI do it.

---

## Link entry reference

```yaml
- id: '12345'             # required — unique numeric string (from upstream source)
  provider: twitter       # required — short source name, no spaces (e.g. shodan, hunter)
  display: Twitter Search # required — human-readable label shown in the UI
  url: "https://twitter.com/search?q={value:urlEncode}"  # required — see URL templates below
  types: [name, alias, hashtag]  # required — list of input types this link accepts
  payWall: Free           # required — one of: Free | Freemium | Paid
  region: Global          # optional — defaults to "Global"
  priority: 0             # optional — sort weight; higher = shown first; defaults to 0
  description: ""         # optional — freeform note shown in the UI
  autorun: false          # optional — true to run automatically on input; defaults to false
```

### Valid `types` values

| Type | Description |
|---|---|
| `name` | Full person name |
| `alias` | Username / handle |
| `domain` | Domain name (e.g. `example.com`) |
| `email-address` | Email address |
| `ip-address` | IPv4 address |
| `IPV6` | IPv6 address |
| `phone-number` | Phone number |
| `hashtag` | Hashtag (without `#`) |
| `url` | Full URL |
| `gps-coordinates` | Lat/long pair |
| `crypto-address` | Cryptocurrency wallet address |
| `VIN` | Vehicle Identification Number |
| `hash` | File hash (MD5, SHA1, SHA256, etc.) |
| `any` | Accepts any input |

### Valid `payWall` values

| Value | Meaning |
|---|---|
| `Free` | Fully free, no account needed |
| `Freemium` | Free tier with limits, or free with account |
| `Paid` | Requires a paid subscription |

---

## URL templates

URLs can include placeholders that are replaced with the user's input before
the link is opened:

| Syntax | Result |
|---|---|
| `{value}` | Raw input value |
| `{value:urlEncode}` | URL-encoded (`%20` etc.) |
| `{value:lower}` | Lowercase |
| `{value:upper}` | Uppercase |
| `{value:base64}` | Base64-encoded |
| `{value:stripPunct}` | Remove all non-alphanumeric characters |
| `{value:spaceToNothing}` | Remove spaces |
| `{value:spaceToDash}` | Replace spaces with `-` |
| `{value:spaceToDot}` | Replace spaces with `.` |
| `{value:firstName}` | First word of a full name |
| `{value:lastName}` | Last word of a full name |
| `{value:userFromEmail}` | Part before `@` in an email |
| `{value:domainFromEmail}` | Part after `@` in an email |
| `{value:noEncoding}` | Explicit no-op (same as `{value}`) |
| `{value:firstIP}` | First IP from a range or CIDR |

Multiple placeholders can appear in one URL:
```
https://example.com/{value:firstName}-{value:lastName}
```

---

## Category files

| File | Category |
|---|---|
| `archives-press.yaml` | Archives & Press |
| `environment-science.yaml` | Environment & Science |
| `government-legal.yaml` | Government & Legal |
| `hash-cracking.yaml` | Hash Cracking |
| `historical.yaml` | Historical |
| `maps.yaml` | Maps |
| `network-scanning.yaml` | Network Scanning |
| `people-search.yaml` | People Search |
| `search-files.yaml` | Search & Files |
| `social-profiles.yaml` | Social Profiles |
| `social-video.yaml` | Social & Video |
| `threat-intelligence.yaml` | Threat Intelligence |
| `username-search.yaml` | Username Search |
| `validation-tools.yaml` | Validation & Tools |
| `vehicle-lookup.yaml` | Vehicle Lookup |
| `whois-dns.yaml` | WHOIS & DNS |

To add a new category: create a new YAML file and add the filename-to-category
mapping in `build.py` under `FILENAME_TO_CATEGORY`.

---

## Running the build locally

```bash
pip install pyyaml

# Validate + compile
python build.py

# Validate only (no output written)
python build.py --check
```
