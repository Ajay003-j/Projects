import requests,re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import random
import sys
from typing import List, Dict, Any

OKBLUE = '\033[94m'
ENDC = '\033[0m'
BOLD = '\033[1m'
OKGREEN = '\033[92m'

SELENIUM_AVAILABLE = False
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    pass

# -------------------------
# Helpers (UNCHANGED)
# -------------------------
def same_domain(base: str, target: str) -> bool:
    return urlparse(base).netloc == urlparse(target).netloc

def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    clean = parsed._replace(fragment="").geturl()
    return clean.rstrip("/")

def create_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(20)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def fetch_page(url: str, driver=None, use_selenium_first: bool = True):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    if use_selenium_first and driver:
        try:
            driver.get(url)
            time.sleep(2)
            return BeautifulSoup(driver.page_source, "html.parser")
        except:
            pass
    try:
        resp = requests.get(url, timeout=10, headers=headers)
        if resp.status_code == 200:
            return BeautifulSoup(resp.text, "html.parser")
    except:
        pass
    return None

def get_urls(start_url: str, max_pages: int = 100, max_depth: int = 3, max_time: int = 600) -> List[str]:
    try:
        visited = set()
        queue = deque([(start_url, 0)])
        start_time = time.time()
        BAD_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico", ".css", ".js", ".pdf", ".zip", ".rar")
        driver = create_driver() if SELENIUM_AVAILABLE else None
        while queue and len(visited) < max_pages:
            if time.time() - start_time > max_time:
                print("⏰ Crawl time limit reached, stopping.")
                break
            current_url, depth = queue.popleft()
            current_url = normalize_url(current_url)
            if current_url in visited or depth > max_depth:
                continue
            soup = fetch_page(current_url, driver, use_selenium_first=True)
            if not soup:
                continue
            visited.add(current_url)
            print(f"{OKGREEN}[+]{ENDC}{OKBLUE}{BOLD}Crawling: {current_url}" + ENDC)
            for link in soup.find_all("a", href=True):
                full_url = urljoin(current_url, link["href"])
                full_url = normalize_url(full_url)
                if full_url.lower().endswith(BAD_EXTENSIONS):
                    continue
                parsed = urlparse(full_url)
                if same_domain(start_url, full_url) and parsed.scheme in ["http", "https"] and full_url not in visited and depth + 1 <= max_depth:
                    queue.append((full_url, depth + 1))
            if len(visited) >= max_pages:
                break
            time.sleep(random.uniform(0.3, 1))
        if driver:
            driver.quit()
        return list(visited)
    except KeyboardInterrupt:
        sys.exit(0)

# -------------------------
# ENHANCED Form Detection
# -------------------------
def detect_form_type(soup, form, page_url) -> str:
    """Detect form purpose: login, signup, search, contact, etc."""
    form_text = soup.get_text().lower()
    form_id = form.get('id', '').lower()
    form_class = form.get('class', [''])[0].lower() if form.get('class') else ''
    action = form.get('action', '').lower()
    
    patterns = {
        'login': ['login', 'signin', 'log in', 'sign in', 'auth', 'authenticate', 'username', 'password'],
        'signup': ['signup', 'sign up', 'register', 'create account', 'registration'],
        'search': ['search', 'q=', 'query', 'find', 'lookup'],
        'contact': ['contact', 'email', 'message', 'feedback', 'support'],
        'comment': ['comment', 'post comment', 'reply'],
        'admin': ['admin', 'dashboard', 'panel', 'moderator'],
        'user': ['profile', 'update profile', 'user settings'],
        'generic': ['input', 'submit', 'send']
    }
    
    inputs = form.find_all(['input', 'textarea'])
    input_names = [inp.get('name', '').lower() for inp in inputs]
    input_types = [inp.get('type', '').lower() for inp in inputs]
    
    form_score = {}
    for form_type, keywords in patterns.items():
        score = 0
        if any(kw in form_id or kw in form_class or kw in action for kw in keywords):
            score += 3
        if any(name in input_names for name in keywords):
            score += 2
        if any(typ in input_types for typ in ['password', 'email'] if form_type in ['login', 'signup']):
            score += 2
        form_score[form_type] = score
    
    return max(form_score, key=form_score.get)

def get_input_forms(URL: str) -> List[Dict[str, Any]]:
    try:
        print(OKBLUE + BOLD + f"🐝 Spidering {URL}..." + ENDC)
        print(OKGREEN+">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"+ENDC)
        urls = get_urls(URL,max_pages=30)
        print(OKBLUE + f"📄 Found {len(urls)} pages to scan" + ENDC)
        results = []
        driver = create_driver() if SELENIUM_AVAILABLE else None
        for page_url in urls:
            soup = fetch_page(page_url, driver, use_selenium_first=True)
            if not soup:
                continue
            forms = soup.find_all("form")
            for form in forms:
                method = form.get("method", "GET").upper()
                action = form.get("action")
                if action:
                    endpoint = urljoin(page_url, action)
                else:
                    endpoint = page_url
                endpoint = normalize_url(endpoint)
                
                # ENHANCED DETECTION
                form_type = detect_form_type(soup, form, page_url)
                inputs = []
                for inp in form.find_all(['input', 'textarea', 'select']):
                    name = inp.get('name', '') or inp.get('id', '')
                    typ = inp.get('type', 'text')
                    placeholder = inp.get('placeholder', '')
                    inputs.append({'name': name, 'type': typ, 'placeholder': placeholder})
                
                results.append({
                    "endpoint": endpoint,
                    "method": method,
                    "action": endpoint,
                    "form_type": form_type,
                    "inputs": inputs
                })
        if driver:
            driver.quit()
        print(OKBLUE + BOLD + f"✅ Found {len(results)} smart attack surfaces!" + ENDC)
        return results
    except KeyboardInterrupt:
        sys.exit(0)