#!/usr/bin/env python3
"""scout.py — see where a username exists across public sites.

username-scout asks 15 public websites one simple question: "does a
profile with this username exist?" Use it to pick a handle for a new
account, or to audit where your own name already appears.

Every supported site was verified by hand to answer 200 for a real
profile and 404 for a missing one — sites that block bots or answer
"yes" for anyone (npm, Reddit, Telegram, Medium, PyPI...) are excluded
on purpose, because a tool that lies is worse than a short list.

Usage:
    python scout.py <username>          # scan all sites
    python scout.py <username> --json   # machine-readable output
    python scout.py --list-sites        # show every supported site

Ethics: this tool reads no private data, logs into nothing, and bypasses
nothing — it only notes whether a public profile page exists. Use it for
handles you have a legitimate interest in (picking your own, checking
your own footprint) and respect each site's terms of service.
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

TOOL_UA = "Mozilla/5.0 (compatible; username-scout/1.0; +https://github.com/RahmaanQuresh/username-scout)"

# Each entry: the URL to check ({u} = username) and the nicer profile URL
# to show people. A 200 response means the profile exists, 404 means the
# username looks free, anything else is reported as unclear, not guessed.
SITES = [
    {"name": "GitHub",      "url": "https://api.github.com/users/{u}",     "profile": "https://github.com/{u}"},
    {"name": "Chess.com",   "url": "https://api.chess.com/pub/player/{u}", "profile": "https://www.chess.com/member/{u}"},
    {"name": "Codewars",    "url": "https://www.codewars.com/users/{u}",   "profile": "https://www.codewars.com/users/{u}"},
    {"name": "AtCoder",     "url": "https://atcoder.jp/users/{u}",         "profile": "https://atcoder.jp/users/{u}"},
    {"name": "RubyGems",    "url": "https://rubygems.org/profiles/{u}",    "profile": "https://rubygems.org/profiles/{u}"},
    {"name": "Docker Hub",  "url": "https://hub.docker.com/u/{u}",         "profile": "https://hub.docker.com/u/{u}"},
    {"name": "Keybase",     "url": "https://keybase.io/{u}",               "profile": "https://keybase.io/{u}"},
    {"name": "SoundCloud",  "url": "https://soundcloud.com/{u}",           "profile": "https://soundcloud.com/{u}"},
    {"name": "Vimeo",       "url": "https://vimeo.com/{u}",                "profile": "https://vimeo.com/{u}"},
    {"name": "Flickr",      "url": "https://www.flickr.com/people/{u}",    "profile": "https://www.flickr.com/people/{u}"},
    {"name": "DeviantArt",  "url": "https://www.deviantart.com/{u}",       "profile": "https://www.deviantart.com/{u}"},
    {"name": "Kaggle",      "url": "https://www.kaggle.com/{u}",           "profile": "https://www.kaggle.com/{u}"},
    {"name": "Gravatar",    "url": "https://en.gravatar.com/{u}.json",     "profile": "https://gravatar.com/{u}"},
    {"name": "WordPress",   "url": "https://profiles.wordpress.org/{u}/",  "profile": "https://profiles.wordpress.org/{u}/"},
    {"name": "Blogger",     "url": "https://{u}.blogspot.com/",            "profile": "https://{u}.blogspot.com/"},
]

FOUND, FREE, UNCLEAR, ERROR = "found", "free", "unclear", "error"

MARKS = {FOUND: "found ", FREE: " free ", UNCLEAR: "  ?   ", ERROR: "  !   "}


def http_status(url: str, timeout: float) -> int:
    """Fetch a URL and return its HTTP status code, or -1 if unreachable."""
    request = urllib.request.Request(url, headers={"User-Agent": TOOL_UA})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code
    except Exception:
        return -1


def classify(status: int) -> str:
    """Map an HTTP status to found / free / unclear / error."""
    if status < 0:
        return ERROR
    if status == 200:
        return FOUND
    if status == 404:
        return FREE
    return UNCLEAR


def check_site(site: dict, username: str, timeout: float = 10.0, fetch=http_status) -> dict:
    """Check one site for one username and return a result record."""
    quoted = quote(username, safe="")
    url = site["url"].format(u=quoted)
    try:
        status = fetch(url, timeout)
    except Exception:
        status = -1
    return {
        "site": site["name"],
        "profile": site["profile"].format(u=quoted),
        "status": status,
        "result": classify(status),
    }


def scan(username: str, timeout: float = 10.0, workers: int = 8, fetch=http_status) -> list[dict]:
    """Check every site in parallel and return results in SITES order."""
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(check_site, site, username, timeout, fetch) for site in SITES]
        return [future.result() for future in futures]


def print_report(results: list[dict]) -> None:
    """Print a fixed-width, human-readable table of results."""
    print(f"{'result':<8}{'site':<14}profile")
    for record in results:
        print(f"{MARKS[record['result']]:<8}{record['site']:<14}{record['profile']}")
    counts = Counter(record["result"] for record in results)
    print(
        "\nfound = profile exists   free = username looks available\n"
        "? = site blocked us or gave an odd answer   ! = could not reach site\n"
        f"\n{counts.get(FOUND, 0)} found, {counts.get(FREE, 0)} free, "
        f"{counts.get(UNCLEAR, 0)} unclear, {counts.get(ERROR, 0)} unreachable"
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Check where a username exists across public sites.")
    parser.add_argument("username", nargs="?", help="the username to look for")
    parser.add_argument("--json", action="store_true", help="print results as JSON")
    parser.add_argument("--timeout", type=float, default=10.0,
                        help="seconds to wait per site (default 10)")
    parser.add_argument("--list-sites", action="store_true",
                        help="list every supported site and exit")
    args = parser.parse_args(argv)

    if args.list_sites:
        for site in SITES:
            print(f"{site['name']:<14}{site['profile']}")
        return 0

    if not args.username or not args.username.strip():
        parser.error("please give a username, e.g. python scout.py torvalds")
    username = args.username.strip()[:64]

    print(f"Scanning {len(SITES)} sites for '{username}'...\n")
    results = scan(username, timeout=args.timeout)

    if args.json:
        print(json.dumps({"username": username, "results": results}, indent=2))
        return 0

    print_report(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
