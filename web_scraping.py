from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def get_urls(URL):
    # launch headless browser
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    driver.get(URL)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # get href links from the html and store them in a list
    urls = [tags.get("href") for tags in soup.find_all("a", href=True) if tags.get("href") != "#"]

    # checking the links are full url or just a path
    Urls = []
    for end_url in urls:
        full_url = urljoin(URL, end_url)
        if full_url.startswith(URL):  # keep only internal links
            Urls.append(full_url)

    driver.quit()
    return Urls

def get_input_forms(URL):

    urls = get_urls(URL)
    results = []
    # launch browser once for form extraction
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    for Url in urls:
        try:
            driver.get(Url)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            forms = soup.find_all("form")
            for form in forms:
                # normalize method and action
                method = form.get("method","get").lower()
                action = form.get("action")
                if action:
                    action = urljoin(Url, action)
                else:
                    action = Url

                results.append({
                    "page": Url,
                    "method": method,
                    "action": action
                })
        except Exception as e:
            print(f"Error fetching {Url}: {e}")

    driver.quit()
    return results
