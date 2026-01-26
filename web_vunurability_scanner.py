from web_scraping import get_input_forms
from proxy import get_proxies
from fake_headers import Headers
from threading import Thread
from itertools import cycle
import requests
import sys
import time
#import curses

#stdsr = curses.initscr()

#TODO make this as a tool in linux
def version():
    print("\n ________  _______   _______   ________      ")
    print(r"|\   __  \|\  ___ \ |\  ___ \ |\   ____\     ")
    print(r"\ \  \|\ /\ \   __/|\ \   __/|\ \  \___|_    ")
    print(r"\ \   __  \ \  \_|/_\ \  \_|/_\ \_____  \     ")
    print(r"  \ \  \|\  \ \  \_|\ \ \  \_|\ \|____|\  \  ")
    print(r"   \ \_______\ \_______\ \_______\____\_\  \ ")
    print(r"    \|_______|\|_______|\|_______|\_________\ ")
    print(r"                                 \|_________|")
    print("\nThis tool is to find the common vunurabilities in website\n")
    print("Bees v1")
    print("version 1.1\n")

def user_input():
    #get the input from the command line check the user input length
    #if the length is less than excepted then exit the code and say the user how to use it
    if len(sys.argv) < 2:
        print("Usage: Bees <url> -flag(s)\nUse -h or --help for help, -v or --version for version")
        sys.exit(1)

    # Handle help/version flags first
    if sys.argv[1] in ['-h', '--help']:
        print("\nUsage: Bees https://example.com -flag or Bees https://example.com -flag -flag\n")
        print("flag -cmd  : scan for command injection")
        print("flag -ssrf : scan for SSRF vulnerability")
        print("flag -xss  : scan for XSS vulnerability")
        print("flag -sql  : scan for SQL injection")
        print("flag -dir  : scan for directory traversal")
        print("flag --full: scan for all common vulnerabilities\n")
        sys.exit(0)

    elif sys.argv[1] in ['-v', '--version']:
        version()
        sys.exit(0)

    # Now enforce URL + flags
    if len(sys.argv) < 3:
        print("Usage: Bees <url> -flag(s)\nUse -h or --help for help, -v or --version for version")
        sys.exit(1)

    version()
    url = sys.argv[1]
    return url

def generate_fake_headers():
    #generate fake headers and return it
    headers = Headers(headers=True).generate()
    return headers

def read_proxies():
    #get_porxies function gets the proxyies need to send the request to the site to avoid blocking ip
    result = get_proxies()
    if result == 1:
        pass
        return []
    else:
        proxies = []
        with open("proxy.txt","r") as f:
            for proxy in f:
                proxy.strip()
                protocol = proxy.split(":")[0]
                proxies.append({protocol:proxy})
        return proxies
            
def send_request(proxy,url):
    #loop through all the endpoints in the website to check all the endpoints in a site
    session = requests.Session()
    url_endpoints,input_tags = get_input_forms(url)
    for endpoint in url_endpoints:
        header = generate_fake_headers()
        time.sleep(2)
        #wait for two second before sending the request to prevent from dos
        full_scan = []
        with open ('sql.txt','r') as f:
            for payload in f:
                full_scan.append(payload)
        try:
            if sys.argv[2] == '-full':
                response = requests.post(endpoint,proxies=proxy,headers=header,params=full_scan)
                print(response.status_code)
        except Exception as e:
            print(f"Check the url is correct {endpoint}: ", e)

def main():
    try:
        url = user_input()
        proxies = read_proxies()
        proxy = cycle(proxies)
        for thread in range(6):
            thead = Thread(target=send_request,args=(next(proxy),url))
            thead.start()
    except KeyboardInterrupt:
        print()

if __name__ == "__main__":
    main()
