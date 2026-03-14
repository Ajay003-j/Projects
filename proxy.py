#!/usr/bin/env python3
"""
proxy.py — Multi-source proxy fetcher with validation
Sources (tried in order, falls back if one is down):
  1. pubproxy.com API
  2. proxyscrape.com API
  3. openproxylist.net API
  4. github raw proxy lists (always available)
"""

import time
import os
import re
import requests

# ─────────────────────────────────────────────
# Proxy Sources
# ─────────────────────────────────────────────

def _fetch_pubproxy() -> list:
    """pubproxy.com — returns one proxy per call, elite only."""
    try:
        r = requests.get(
            "http://pubproxy.com/api/proxy?level=elite&type=http",
            timeout=5
        )
        if r.status_code == 200 and r.text.strip():
            data = r.json()
            entry = data["data"][0]
            return [f"{entry['type'].lower()}://{entry['ipPort']}"]
    except Exception:
        pass
    return []


def _fetch_proxyscrape() -> list:
    """proxyscrape.com — returns a plain text list of ip:port."""
    try:
        r = requests.get(
            "https://api.proxyscrape.com/v2/?request=getproxies"
            "&protocol=http&timeout=5000&country=all&ssl=all&anonymity=elite",
            timeout=8
        )
        if r.status_code == 200 and r.text.strip():
            proxies = []
            for line in r.text.strip().splitlines():
                line = line.strip()
                if re.match(r"\d+\.\d+\.\d+\.\d+:\d+", line):
                    proxies.append(f"http://{line}")
            return proxies
    except Exception:
        pass
    return []


def _fetch_openproxylist() -> list:
    """openproxylist.net — plain text list."""
    try:
        r = requests.get(
            "https://openproxylist.net/http.txt",
            timeout=8
        )
        if r.status_code == 200 and r.text.strip():
            proxies = []
            for line in r.text.strip().splitlines():
                line = line.strip()
                if re.match(r"\d+\.\d+\.\d+\.\d+:\d+", line):
                    proxies.append(f"http://{line}")
            return proxies
    except Exception:
        pass
    return []


def _fetch_github_list() -> list:
    """
    Raw proxy lists from GitHub — large, always available.
    These are community-maintained and updated frequently.
    """
    urls = [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    ]
    proxies = []
    for url in urls:
        try:
            r = requests.get(url, timeout=8)
            if r.status_code == 200 and r.text.strip():
                for line in r.text.strip().splitlines():
                    line = line.strip()
                    if re.match(r"\d+\.\d+\.\d+\.\d+:\d+", line):
                        proxies.append(f"http://{line}")
                if proxies:
                    break   # got a list — no need for more sources
        except Exception:
            continue
    return proxies


# Sources in priority order
PROXY_SOURCES = [
    ("pubproxy.com",      _fetch_pubproxy),
    ("proxyscrape.com",   _fetch_proxyscrape),
    ("openproxylist.net", _fetch_openproxylist),
    ("github lists",      _fetch_github_list),
]

# ─────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────

def _validate_proxy(proxy_str: str, timeout: int = 5) -> bool:
    """
    Test proxy by making a real request through it.
    Uses httpbin.org/ip — returns your IP as JSON.
    If the proxy works, we get a 200 response.
    """
    try:
        proto = proxy_str.split("://")[0]
        resp  = requests.get(
            "http://httpbin.org/ip",
            proxies={proto: proxy_str},
            timeout=timeout
        )
        return resp.status_code == 200
    except Exception:
        return False

# ─────────────────────────────────────────────
# Main Function
# ─────────────────────────────────────────────

def get_proxies(max_proxies: int = 10, output_file: str = "proxy.txt") -> list:
    """
    Fetch working elite proxies from multiple sources.
    Tries each source in order until we have enough.
    Validates every proxy before saving.
    Returns list of proxy strings like ["http://1.2.3.4:8080", ...]
    """
    # Load already known proxies to avoid duplicates
    known_proxies: set = set()
    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            known_proxies = set(line.strip() for line in f if line.strip())

    collected: list = list(known_proxies)

    if len(collected) >= max_proxies:
        return collected

    # Try each source
    for source_name, fetch_fn in PROXY_SOURCES:
        if len(collected) >= max_proxies:
            break

        print(f"[proxy] Trying source: {source_name}...")
        candidates = []

        try:
            candidates = fetch_fn()
        except Exception as e:
            print(f"[proxy] {source_name} failed: {e}")
            continue

        if not candidates:
            print(f"[proxy] {source_name} returned nothing — trying next source")
            continue

        print(f"[proxy] {source_name} → {len(candidates)} candidates, validating...")

        # Validate each candidate
        for proxy_str in candidates:
            if len(collected) >= max_proxies:
                break
            if proxy_str in known_proxies:
                continue

            if _validate_proxy(proxy_str):
                known_proxies.add(proxy_str)
                collected.append(proxy_str)
                # Save immediately so progress isn't lost on interrupt
                with open(output_file, "a") as f:
                    f.write(proxy_str + "\n")
                print(f"[proxy] ✓ {proxy_str} ({len(collected)}/{max_proxies})")
            else:
                print(f"[proxy] ✗ dead: {proxy_str}")

            time.sleep(0.3)   # small delay between validation requests

        if len(collected) >= max_proxies:
            break

        print(f"[proxy] {source_name} exhausted — have {len(collected)}/{max_proxies}")

    if len(collected) < max_proxies:
        print(f"[proxy] ⚠  Could only find {len(collected)} working proxies "
              f"(wanted {max_proxies}) — using what we have")

    return collected


if __name__ == "__main__":
    # Run directly to test: python3 proxy.py
    print("Fetching 5 proxies...")
    proxies = get_proxies(max_proxies=5)
    print(f"\nResult: {len(proxies)} proxies")
    for p in proxies:
        print(f"  {p}")