from bs4 import BeautifulSoup
import requests

def get_urls(URL):
    #send the request to the site to get the response and get the html
    response = requests.get(URL)
    soup = BeautifulSoup(response.content,"html.parser")
    #get the herf links from the html and store that in a list
    urls = [tags.get("href") for tags in  soup.find_all("a",href=True) if tags.get("href") != "#"]
    #checking the links are full url or just a path
    Urls = []
    for Url in urls:
        if URL not in Url: 
            #check the user give url ends with / and remove it to avoid // 
            #if any one of the liks is not full url then make it as full url
            #append the full url to the list and return it
            if URL[-1] == "/":
                URL = URL[:-1]
                Urls.append(URL+Url)
            else:
                Urls.append(URL+Url)
        else:
            #return the url if it is full url
            return Url
    return Urls

def get_input_forms(URL):
    urls = get_urls(URL)
    for Url in urls:
        response = requests.get(url=Url)
        soup = BeautifulSoup(response.content,"html.parser")
        tag = [tags for tags in soup.find_all("input")]
        packing = Url,tag
    return packing
