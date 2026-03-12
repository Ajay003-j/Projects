"""
web_scraping.py - Professional-grade crawler (SQLMap/Nuclei level)
Improvements:
  - Proper URL deduplication using parameter-normalized fingerprints
  - robots.txt respect
  - JS link extraction
  - Smarter form detection
  - No silent exception swallowing
  - Single Selenium driver lifecycle
"""

import re
import sys
import time
import random
import logging
from typing import List, Dict, Any, Optional, Set
from collections import deque
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

import requests
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S"
)
log = logging.getLogger("crawler")

OKBLUE  = '\033[94m'
ENDC    = '\033[0m'
BOLD    = '\033[1m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL    = '\033[91m'

# ─────────────────────────────────────────────
# Selenium (optional)
# ─────────────────────────────────────────────
SELENIUM_AVAILABLE = False
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import WebDriverException, TimeoutException
    SELENIUM_AVAILABLE = True
except ImportError:
    pass

BAD_EXTENSIONS = (
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico",
    ".css", ".js", ".pdf", ".zip", ".rar", ".mp4",
    ".mp3", ".woff", ".woff2", ".ttf", ".eot", ".map"
)

# ─────────────────────────────────────────────
# URL Utilities
# ─────────────────────────────────────────────

def same_domain(base: str, target: str) -> bool:
    return urlparse(base).netloc == urlparse(target).netloc

def normalize_url(url: str) -> str:
    """Strip fragment, trailing slash."""
    parsed = urlparse(url)
    clean = parsed._replace(fragment="").geturl()
    return clean.rstrip("/")

def url_fingerprint(url: str) -> str:
    """
    SQLMap-style URL deduplication:
    Two URLs with the same path and same parameter NAMES
    (regardless of values) are treated as duplicates.
    e.g. /page?id=1 and /page?id=99 → same fingerprint
    """
    parsed = urlparse(url)
    params = sorted(parse_qs(parsed.query).keys())
    normalized = parsed._replace(
        query="&".join(f"{k}=" for k in params),
        fragment=""
    )
    return urlunparse(normalized).rstrip("/")

def is_bad_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return True
    if any(parsed.path.lower().endswith(ext) for ext in BAD_EXTENSIONS):
        return True
    # Skip logout/signout to avoid breaking session
    if any(x in url.lower() for x in ["logout", "signout", "logoff"]):
        return True
    return False

# ─────────────────────────────────────────────
# robots.txt
# ─────────────────────────────────────────────

def load_robots(base_url: str, respect_robots: bool = True) -> Optional[RobotFileParser]:
    if not respect_robots:
        return None
    try:
        rp = RobotFileParser()
        robots_url = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}/robots.txt"
        rp.set_url(robots_url)
        rp.read()
        log.info(f"robots.txt loaded from {robots_url}")
        return rp
    except Exception as e:
        log.warning(f"Could not load robots.txt: {e}")
        return None

def robots_allowed(rp: Optional[RobotFileParser], url: str) -> bool:
    if rp is None:
        return True
    return rp.can_fetch("*", url)

# ─────────────────────────────────────────────
# Selenium Driver
# ─────────────────────────────────────────────

def create_driver() -> Optional[object]:
    if not SELENIUM_AVAILABLE:
        return None
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-images")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(15)
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        log.info(f"{OKGREEN}Chrome driver ready{ENDC}")
        return driver
    except Exception:
        log.warning("Selenium unavailable, using requests only")
        return None

# ─────────────────────────────────────────────
# Page Fetching
# ─────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def fetch_page(
    url: str,
    session: requests.Session,
    driver=None,
    use_selenium: bool = True,
    timeout: int = 10,
) -> Optional[BeautifulSoup]:
    """
    Fetch page with Selenium first (for JS), fallback to requests.
    Returns BeautifulSoup or None. Never silently swallows all errors.
    """
    if use_selenium and driver:
        try:
            driver.get(url)
            time.sleep(1.5)
            return BeautifulSoup(driver.page_source, "html.parser")
        except TimeoutException:
            log.debug(f"Selenium timeout on {url}, falling back to requests")
        except WebDriverException as e:
            log.debug(f"Selenium error on {url}: {e}")

    try:
        resp = session.get(url, timeout=timeout, headers=HEADERS, allow_redirects=True)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except requests.exceptions.HTTPError as e:
        log.debug(f"HTTP error {e} on {url}")
    except requests.exceptions.ConnectionError:
        log.debug(f"Connection error on {url}")
    except requests.exceptions.Timeout:
        log.debug(f"Request timeout on {url}")
    except Exception as e:
        log.debug(f"Unexpected fetch error on {url}: {e}")
    return None

# ─────────────────────────────────────────────
# JS Link Extraction (like Burp/SQLMap)
# ─────────────────────────────────────────────

JS_URL_PATTERN = re.compile(
    r"""(?:href|src|action|url|endpoint|api)\s*[:=]\s*['"]([^'"]+)['"]""",
    re.IGNORECASE
)
RELATIVE_PATH_PATTERN = re.compile(r"""['"](\/?[\w\-/]+\.(?:php|asp|aspx|jsp|html|do|action))['"]""")

def extract_js_links(soup: BeautifulSoup, base_url: str) -> Set[str]:
    """Extract URLs from inline JS and script tags — like Burp Suite passive scan."""
    found = set()
    for script in soup.find_all("script"):
        js_text = script.get_text()
        for match in JS_URL_PATTERN.finditer(js_text):
            url = urljoin(base_url, match.group(1))
            found.add(normalize_url(url))
        for match in RELATIVE_PATH_PATTERN.finditer(js_text):
            url = urljoin(base_url, match.group(1))
            found.add(normalize_url(url))
    return found

# ─────────────────────────────────────────────
# Crawler
# ─────────────────────────────────────────────

def get_urls(
    start_url: str,
    max_pages: int = 100,
    max_depth: int = 3,
    max_time: int = 600,
    respect_robots: bool = True,
) -> List[str]:
    """
    BFS crawler with:
    - Parameter-normalized URL deduplication (SQLMap-style)
    - robots.txt support
    - JS link extraction
    - Single driver lifecycle
    - Proper error logging
    """
    try:
        session     = requests.Session()
        driver      = create_driver() if SELENIUM_AVAILABLE else None
        rp          = load_robots(start_url, respect_robots)
        visited_fps : Set[str] = set()   # fingerprints (param-normalized)
        visited_urls: Set[str] = set()   # actual URLs for output
        queue       = deque([(normalize_url(start_url), 0)])
        start_time  = time.time()

        while queue and len(visited_urls) < max_pages:
            if time.time() - start_time > max_time:
                log.warning("Crawl time limit reached")
                break

            current_url, depth = queue.popleft()
            fp = url_fingerprint(current_url)

            if fp in visited_fps or depth > max_depth:
                continue
            if is_bad_url(current_url):
                continue
            if not robots_allowed(rp, current_url):
                log.debug(f"robots.txt blocked: {current_url}")
                continue

            soup = fetch_page(current_url, session, driver, use_selenium=True)
            if not soup:
                continue

            visited_fps.add(fp)
            visited_urls.add(current_url)
            log.info(f"{OKGREEN}[+]{ENDC} {OKBLUE}{BOLD}Crawled [{len(visited_urls)}/{max_pages}]: {current_url}{ENDC}")

            # 1. Standard anchor links
            new_links: Set[str] = set()
            for tag in soup.find_all("a", href=True):
                full = normalize_url(urljoin(current_url, tag["href"]))
                new_links.add(full)

            # 2. Form action endpoints
            for form in soup.find_all("form", action=True):
                full = normalize_url(urljoin(current_url, form["action"]))
                new_links.add(full)

            # 3. JS-embedded links (Burp-style passive extraction)
            js_links = extract_js_links(soup, current_url)
            new_links.update(js_links)

            for link in new_links:
                if (
                    same_domain(start_url, link)
                    and not is_bad_url(link)
                    and url_fingerprint(link) not in visited_fps
                    and depth + 1 <= max_depth
                ):
                    queue.append((link, depth + 1))

            time.sleep(random.uniform(0.2, 0.8))

        if driver:
            driver.quit()

        log.info(f"Crawl complete: {len(visited_urls)} unique pages")
        return list(visited_urls)

    except KeyboardInterrupt:
        log.info("Crawl interrupted by user")
        sys.exit(0)

# ─────────────────────────────────────────────
# Form Detection
# ─────────────────────────────────────────────

FORM_TYPE_PATTERNS = {
    "login":   ["login", "signin", "sign in", "log in", "auth", "password"],
    "signup":  ["signup", "register", "registration", "create account"],
    "search":  ["search", "query", "find", "lookup", "q="],
    "contact": ["contact", "feedback", "support", "message"],
    "comment": ["comment", "reply", "post"],
    "admin":   ["admin", "dashboard", "panel"],
    "upload":  ["upload", "file", "attachment"],
}

def detect_form_type(form: Any, page_url: str) -> str:
    form_id     = (form.get("id",     "") or "").lower()
    form_class  = " ".join(form.get("class", []) or []).lower()
    action      = (form.get("action", "") or "").lower()
    inputs      = form.find_all(["input", "textarea", "select"])
    input_names = " ".join(
        (inp.get("name", "") or inp.get("id", "") or "").lower()
        for inp in inputs
    )
    combined = f"{form_id} {form_class} {action} {input_names}"

    scores = {ft: 0 for ft in FORM_TYPE_PATTERNS}
    for ft, keywords in FORM_TYPE_PATTERNS.items():
        for kw in keywords:
            if kw in combined:
                scores[ft] += 1

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "generic"

def extract_inputs(form: Any) -> List[Dict[str, str]]:
    inputs = []
    for inp in form.find_all(["input", "textarea", "select"]):
        name = inp.get("name") or inp.get("id") or ""
        if not name:
            continue
        inputs.append({
            "name":        name,
            "type":        inp.get("type", "text").lower(),
            "placeholder": inp.get("placeholder", ""),
            "value":       inp.get("value", ""),
        })
    return inputs

# ─────────────────────────────────────────────
# Attack Surface Discovery
# ─────────────────────────────────────────────

def get_input_forms(
    URL: str,
    max_pages: int = 50,
    respect_robots: bool = True,
) -> List[Dict[str, Any]]:
    """
    Discover all attack surfaces:
      1. HTML forms
      2. URL query parameters (as virtual forms)
      3. JS-embedded endpoints
    Returns deduplicated list, capped at 100.
    """
    try:
        log.info(f"{OKBLUE}{BOLD}Spidering {URL}...{ENDC}")
        urls    = get_urls(URL, max_pages=max_pages, respect_robots=respect_robots)
        session = requests.Session()
        driver  = create_driver() if SELENIUM_AVAILABLE else None
        results : List[Dict[str, Any]] = []
        seen_fps: Set[str] = set()

        def add_form(endpoint, method, form_type, inputs, source):
            fp = f"{normalize_url(endpoint)}::{method}::{sorted(i['name'] for i in inputs)}"
            if fp in seen_fps or not inputs:
                return
            seen_fps.add(fp)
            results.append({
                "endpoint":  normalize_url(endpoint),
                "method":    method.upper(),
                "form_type": form_type,
                "inputs":    inputs,
                "source":    source,
            })

        for page_url in urls:
            soup = fetch_page(page_url, session, driver, use_selenium=True)
            if not soup:
                continue

            # ── 1. HTML forms ──────────────────────────────────────
            for form in soup.find_all("form"):
                method   = (form.get("method", "GET") or "GET").upper()
                action   = form.get("action")
                endpoint = normalize_url(urljoin(page_url, action)) if action else normalize_url(page_url)
                ft       = detect_form_type(form, page_url)
                inputs   = extract_inputs(form)
                add_form(endpoint, method, ft, inputs, "html_form")

            # ── 2. Query parameters as virtual GET forms ───────────
            parsed = urlparse(page_url)
            if parsed.query:
                # Use proper parse_qs — handles = in values correctly
                qparams = parse_qs(parsed.query)
                virtual_inputs = [
                    {"name": k, "type": "text", "placeholder": "", "value": v[0]}
                    for k, v in qparams.items()
                ]
                if virtual_inputs:
                    add_form(page_url, "GET", "query_param", virtual_inputs, "url_param")

            # ── 3. JS-discovered endpoints ──────────────────────────
            for js_url in extract_js_links(soup, page_url):
                if not same_domain(URL, js_url):
                    continue
                js_parsed = urlparse(js_url)
                if js_parsed.query:
                    qparams = parse_qs(js_parsed.query)
                    virtual_inputs = [
                        {"name": k, "type": "text", "placeholder": "", "value": v[0]}
                        for k, v in qparams.items()
                    ]
                    if virtual_inputs:
                        add_form(js_url, "GET", "js_endpoint", virtual_inputs, "js_extract")

        if driver:
            driver.quit()

        log.info(f"{OKGREEN}Found {len(results)} unique attack surfaces{ENDC}")
        return results[:100]

    except KeyboardInterrupt:
        log.info("Interrupted")
        sys.exit(0)