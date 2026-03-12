import time
import os
import requests

def get_proxies(max_proxies: int = 10, output_file: str = "proxy.txt") -> list:
    """
    Fetch elite proxies from pubproxy.com and save unique ones to file.
    Returns a list of working proxy strings.
    """
    # Load already-known proxies to avoid duplicates
    known_proxies: set = set()
    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            known_proxies = set(line.strip() for line in f if line.strip())

    collected: list = list(known_proxies)
    attempts = 0
    max_attempts = max_proxies * 3  # Allow retries

    while len(collected) < max_proxies and attempts < max_attempts:
        attempts += 1
        try:
            response = requests.get(
                "http://pubproxy.com/api/proxy?level=elite",
                timeout=5
            )

            if response.status_code != 200 or not response.text.strip():
                print(f"[proxy] Bad response ({response.status_code}), retrying...")
                time.sleep(10)
                continue

            data = response.json()
            entry = data["data"][0]
            proxy_str = f"{entry['type'].lower()}://{entry['ipPort']}"

            if proxy_str in known_proxies:
                time.sleep(2)
                continue

            # Optional: validate the proxy before saving
            if _validate_proxy(proxy_str):
                known_proxies.add(proxy_str)
                collected.append(proxy_str)
                with open(output_file, "a") as f:
                    f.write(proxy_str + "\n")
            else:
                continue

        except (requests.RequestException, KeyError, IndexError, ValueError) as e:
            print(f"[proxy] Error: {e}")
            time.sleep(10)
            continue

        time.sleep(5)  # Rate limit: only sleep after a real request

    return collected


def _validate_proxy(proxy_str: str, test_url: str = "http://httpbin.org/ip", timeout: int = 5) -> bool:
    """Returns True if the proxy is reachable."""
    try:
        protocol = proxy_str.split("://")[0]
        resp = requests.get(
            test_url,
            proxies={protocol: proxy_str},
            timeout=timeout
        )
        return resp.status_code == 200
    except Exception:
        return False