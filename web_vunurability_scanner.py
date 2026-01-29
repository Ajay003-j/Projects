#!/home/stars/projects/.env/bin/python3
from web_scraping import get_input_forms
from proxy import get_proxies
from fake_headers import Headers
from threading import Thread
from itertools import cycle
import requests
import time
import sys
import os
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
#getting the palyods from the file and loading it into the list
def sql_payload():
    sql_payloads = []
    with open ('sql.txt','r') as f:
        for payload in f:
            sql_payloads.append(payload.strip())
        return sql_payloads

def xss_payload():
    xss_payloads = []
    with open ('xss.txt','r') as f:
        for payload in f:
            xss_payloads.append(payload.strip())
        return xss_payloads

def ssrf_payload():
    ssrf_payloads = []
    with open ('ssrf.txt','r') as f:
        for payload in f:
            ssrf_payloads.append(payload.strip())
        return payload

def cmd_payload():
    cmd_payloads = []
    with open ('cmd.txt','r') as f:
        for payload in f:
            cmd_payloads.append(payload.strip())
        return cmd_payloads

def dir_payload():
    dir_payloads = []
    with open ('dir.txt','r') as f:
        for payload in f:
            dir_payloads.append(payload.strip())
        return dir_payloads

def generate_fake_headers():
    #generate fake headers and return it
    headers = Headers(headers=True).generate()
    return headers

def read_proxies():
    #get_porxies function gets the proxyies need to send the request to the site to avoid blocking ip
    #checking the file is empty if empty wait for 6 sesonds 
    file_is_empty = False
    result = get_proxies()
    proxies = []
    with open("proxy.txt","r") as f:

        if os.stat('proxy.txt').st_size != 0:
            if result == 1:
                for proxy in f:
                    proxy.strip()
                    protocol = proxy.split(":")[0]
                    proxies.append({protocol:proxy})
                return proxies
            else:
                for proxy in f:
                    proxy.strip()
                    protocol = proxy.split(":")[0]
                    proxies.append({protocol:proxy})
                    print(proxies)
                return proxies
        else:
            if file_is_empty is True:
                sys.exit(1)
            else:
                file_is_empty = True
                time.sleep(6)
            
def send_request(proxy,url):
    #loop through all the endpoints in the website to check all the endpoints in a site
    session = requests.Session()
    for endpoint,input_tags in get_input_forms(url):
        header = generate_fake_headers()
        time.sleep(2)
        #wait for two second before sending the request to prevent from dos
        try:
            if sys.argv[2] == '--full':
                sql_payloads =sql_payload()
                cmd_payloads = sql_payload()
                ssrf_payloads = ssrf_payload()
                xss_payloads = xss_payload()
                dir_payloads = dir_payload()

                input_tags.get('type')
                print("\nScanning for vulnerability..")
                if endpoint 
                response = requests.get(endpoint,proxies=proxy,headers=header)
                print(response.status_code)
        except Exception as e:
            print(f"Check the url is correct {endpoint}: ", e)

def main():
    try:
        url = user_input()
        proxies = read_proxies()
        proxy = cycle(proxies)
        for threads in range(6):
            thead = Thread(target=send_request,args=(next(proxy),url))
            thead.start()
    except KeyboardInterrupt:
        print()

if __name__ == "__main__":
    main()
