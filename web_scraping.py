from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests

def get_urls(URL):
    #send the request to the site to get the response and get the html
    response = requests.get(URL)
    soup = BeautifulSoup(response.content,"html.parser")
    #get the herf links from the html and store that in a list
    urls = [tags.get("href") for tags in  soup.find_all("a",href=True) if tags.get("href") != "#"]
    #checking the links are full url or just a path
    Urls = []
    for end_url in urls:
        full_url = urljoin(URL, end_url)
        if full_url.startswith(URL):  # keep only internal links
            Urls.append(full_url)

    return Urls
    #if any one of the liks is not full url then make it as full url
    #append the full url to the list and return it
            
def get_input_forms(URL):

    urls = get_urls(URL)
    packing = []
    for Url in urls:
        try:
            response = requests.get(Url)
            soup = BeautifulSoup(response.content,"html.parser")
            forms = soup.find_all("form")
            for form in forms:
                method = form.get("method", "get").lower()
                action = urljoin(Url, form.get("action", Url))
                inputs = [inp for inp in form.find_all("input")]
                packing.append((Url, method, action, inputs))
        except Exception as e:
            print(e)
    return packing
