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

def print_help():
    print("\nUsage: Bees https://example.com -flag or Bees https://example.com -flag -flag\n")
    print("flag -cmd  : scan for command injection")
    print("flag -ssrf : scan for SSRF vulnerability")
    print("flag -xss  : scan for XSS vulnerability")
    print("flag -sql  : scan for SQL injection")
    print("flag -dir  : scan for directory traversal")
    print("flag --full: scan for all common vulnerabilities")
    print("flag --live : watch the attack process in live in terminal")
    print("flage --file : store the attack results in a file named results.txt for later analyisis\n")
    
def user_input():
    #get the input from the command line check the user input length
    #if the length is less than excepted then exit the code and say the user how to use it
    if len(sys.argv) < 2:
        print("Usage: Bees <url> -flag(s)\nUse -h or --help for help, -v or --version for version")
        sys.exit(0)

    # Handle help/version flags first
    if sys.argv[1] in ['-h', '--help']:
        print_help()

    elif sys.argv[1] in ['-v', '--version']:
        version()
        sys.exit(0)

    # Now enforce URL + flags
    if len(sys.argv) < 4:
        print("Usage: Bees <url> -flag(s)\nUse -h or --help for help, -v or --version for version")
        sys.exit(0)
    else:
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
        return ssrf_payloads

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
                return proxies
        else:
            #checking is the file is empty or not if empty sleep for 6 seconds
            if file_is_empty is True:
                sys.exit(1)
            else:
                file_is_empty = True
                time.sleep(6)

def response_handler(response,endpoint,payload):
    #checking the status code and of the web response for the payload
    #checking the user flag input for live output and storeing the output in a file
    if response.status_code in [200,204,301,500,302]:
        if sys.argv[3] == '--live':
            print('------------------------------------------------------------------------')
            print('------------------------------------------------------------------------')
            print(f"\nThis endpoint {endpoint} is vunurable to the payload {payload} response:\t{response.text}\n\n")
        elif sys.argv[3] == 'file':
            with open ('results.txt','a') as f:
                f.write('---------------------------------------------------------------------------------')
                f.write('---------------------------------------------------------------------------------\n')
                f.write(f"This endpoint {endpoint} is vunurable to the payload {payload} response:\t{response.text}\n\n")
        else:
            print_help()

def send_request(proxy,url):
    #loop through all the endpoints in the website to check all the endpoints in a site
    session = requests.Session()
    payloads = []
    for endpoint,method,action,inputs in get_input_forms(url):
        header = generate_fake_headers()
        time.sleep(2)
        #wait for two second before sending the request to prevent from dos
        try:
            #checking the user input flag which type of scan user wanted to do
            sql_payloads =sql_payload()
            cmd_payloads = cmd_payload()
            ssrf_payloads = ssrf_payload()
            xss_payloads = xss_payload()
            dir_payloads = dir_payload()
            if sys.argv[2] == '--full': 
                #checking the methods and actions and modifiing the payloads accoriding to the action
                if method == 'post' and action == 'login':
                    data = {"username": payload, "password": "Test@123:"}
                    payloads = sql_payloads+cmd_payloads+xss_payloads
                    for payload in payloads:
                        response = session.post(endpoint,proxies=proxy,headers=header,data=data)
                        response_handler(response,endpoint,payload)
                    #clearing the list after the scan for avoiding duplicate payloads
                    payloads.clear()

                elif method == 'post' and action == 'signup' or action == 'sigin':
                    payloads = sql_payloads+cmd_payloads+xss_payloads
                    data = {"username":payload,"email":"example@gmail.com","password":"Test@123:"}
                    for payload in payloads:
                        response = session.post(endpoint,proxies=proxy,headers=header,data=data)
                        response_handler(response,endpoint,payload)
                    payloads.clear()

                elif method == 'post' and action not in ['sigin','signup','login']:
                    payloads = sql_payloads+cmd_payloads+xss_payloads
                    for payload in payloads:
                        response = session.post(endpoint,proxies=proxy,headers=header,data=payload)
                        response_handler(response,endpoint,payload)
                    payloads.clear()

                elif method == 'get':
                    payloads = sql_payloads,cmd_payloads+xss_payloads+dir_payloads+ssrf_payloads
                    for payload in payloads:
                        response = session.get(endpoint,proxies=proxy,headers=header,params=payloads)
                        response_handler(response,endpoint,payload)
                    payloads.clear()

                elif method == 'put' and action in ['sigin','sigup']:
                    payloads = sql_payloads+cmd_payloads+xss_payloads
                    data = {"username":payload,"email":"example@gmail.com","password":"Test@123:"}
                    for payload in payloads:
                        response = session.put(endpoint,proxies=proxy,headers=header,data=data)
                        response_handler(response,endpoint,payload)
                    payloads.clear()
                
                elif method == 'put' and action == 'login':
                    data = {"username": payload, "password": "Test@123:"}
                    payloads = sql_payloads+cmd_payloads+xss_payloads
                    for payload in payloads:
                        response = session.post(endpoint,proxies=proxy,headers=header,data=data)
                        response_handler(response,endpoint,payload)
                    #clearing the list after the scan for avoiding duplicate payloads
                    payloads.clear()
                
                elif method == 'put' and action not in ['login','sigin','sigup']:
                    payloads = sql_payloads+cmd_payloads+xss_payloads
                    for payload in payloads:
                        response = session.post(endpoint,proxies=proxy,headers=header,data=payload)
                        response_handler(response,endpoint,payload)
                    #clearing the list after the scan for avoiding duplicate payloads
                    payloads.clear()
                else:
                    sys.exit(1)
            elif sys.argv[2] == '-sql':
                if method == 'post' and action in ['sigin','signup']:
                    payloads.append(sql_payloads)
                    for payload in payloads:
                        data = {"username":payload,"email":"example@gmail.com","password":"Test@123:"}
                        response = session.post(endpoint,proxies=proxy,headers=header,data=data)
                        response_handler(response,endpoint,payload)
                    payloads.clear()

                elif method == 'post' and action == 'login':
                    payloads.append(sql_payloads)
                    for payload in payloads:
                        data = {"username":payload,"email":"example@gmail.com","password":"Test@123:"}
                        response = session.post(endpoint,proxies=proxy,headers=header,data=data)
                        response_handler(response,endpoint,payload)
                    payloads.clear()

                elif method == 'post' and action not in ['sigin','signup','login']:
                    payloads.append(sql_payloads)
                    for payload in payloads:
                        response = session.post(endpoint,proxies=proxy,headers=header,data=payload)
                        response_handler(response,endpoint,payload)
                    payloads.clear()

                elif method == 'get':
                    payloads.append(sql_payloads)
                    for payload in payloads:
                        response = session.get(endpoint,proxies=proxy,headers=header,params=payload)
                        response_handler(response,endpoint,payload)
                    payloads.clear()

                elif method == 'put' and action in ['sigin','sigup']:
                    payloads.append(sql_payloads)
                    data = {"username":payload,"email":"example@gmail.com","password":"Test@123:"}
                    for payload in payloads:
                        response = session.put(endpoint,proxies=proxy,headers=header,data=data)
                        response_handler(response,endpoint,payload)
                    payloads.clear()
                
                elif method == 'put' and action == 'login':
                    data = {"username": payload, "password": "Test@123:"}
                    payloads.append(sql_payload)
                    for payload in payloads:
                        response = session.post(endpoint,proxies=proxy,headers=header,data=data)
                        response_handler(response,endpoint,payload)
                    #clearing the list after the scan for avoiding duplicate payloads
                    payloads.clear()
                
                elif method == 'put' and action not in ['login','sigin','sigup']:
                    payloads.append(sql_payloads)
                    for payload in payloads:
                        response = session.post(endpoint,proxies=proxy,headers=header,data=payload)
                        response_handler(response,endpoint,payload)
                    #clearing the list after the scan for avoiding duplicate payloads
                    payloads.clear()
                else:
                    sys.exit(1)

            elif sys.argv[2] == '-cmd':
                if method == 'post' and action in ['sigin','signup']:
                    payloads.append(cmd_payloads)
                    for payload in payloads:
                        data = {"username":payload,"email":"example@gmail.com","password":"Test@123:"}
                        response = session.post(endpoint,proxies=proxy,headers=header,data=data)
                        response_handler(response,endpoint,payload)
                    payloads.clear()

                elif method == 'post' and action == 'login':
                    payloads.append(cmd_payloads)
                    for payload in payloads:
                        data = {"username":payload,"email":"example@gmail.com","password":"Test@123:"}
                        response = session.post(endpoint,proxies=proxy,headers=header,data=data)
                        response_handler(response,endpoint,payload)
                    payloads.clear()

                elif method == 'post' and action not in ['sigin','signup','login']:
                    payloads.append(cmd_payloads)
                    for payload in payloads:
                        response = session.post(endpoint,proxies=proxy,headers=header,data=payload)
                        response_handler(response,endpoint,payload)
                    payloads.clear()

                elif method == 'get':
                    payloads.append(cmd_payloads)
                    for payload in payloads:
                        response = session.get(endpoint,proxies=proxy,headers=header,params=payload)
                        response_handler(response,endpoint,payload)
                    payloads.clear()

                elif method == 'put' and action in ['sigin','sigup']:
                    payloads.append(cmd_payloads)
                    data = {"username":payload,"email":"example@gmail.com","password":"Test@123:"}
                    for payload in payloads:
                        response = session.put(endpoint,proxies=proxy,headers=header,data=data)
                        response_handler(response,endpoint,payload)
                    payloads.clear()
                
                elif method == 'put' and action == 'login':
                    data = {"username": payload, "password": "Test@123:"}
                    payloads.append(cmd_payload)
                    for payload in payloads:
                        response = session.post(endpoint,proxies=proxy,headers=header,data=data)
                        response_handler(response,endpoint,payload)
                    #clearing the list after the scan for avoiding duplicate payloads
                    payloads.clear()
                
                elif method == 'put' and action not in ['login','sigin','sigup']:
                    payloads.append(cmd_payloads)
                    for payload in payloads:
                        response = session.post(endpoint,proxies=proxy,headers=header,data=payload)
                        response_handler(response,endpoint,payload)
                        #clearing the list after the scan for avoiding duplicate payloads
                    payloads.clear()
                else:
                    sys.exit(1)

            elif sys.argv[2] == '-xss':
                if method == 'post' and action in ['sigin','signup']:
                    payloads.append(xss_payloads)
                    for payload in payloads:
                        data = {"username":payload,"email":"example@gmail.com","password":"Test@123:"}
                        response = session.post(endpoint,proxies=proxy,headers=header,data=data)
                        response_handler(response,endpoint,payload)
                    payloads.clear()

                elif method == 'post' and action == 'login':
                    payloads.append(xss_payloads)
                    for payload in payloads:
                        data = {"username":payload,"email":"example@gmail.com","password":"Test@123:"}
                        response = session.post(endpoint,proxies=proxy,headers=header,data=data)
                        response_handler(response,endpoint,payload)
                    payloads.clear()

                elif method == 'post' and action not in ['sigin','signup','login']:
                    payloads.append(xss_payloads)
                    for payload in payloads:
                        response = session.post(endpoint,proxies=proxy,headers=header,data=payload)
                        response_handler(response,endpoint,payload)
                    payloads.clear()

                elif method == 'get':
                    payloads.append(xss_payloads)
                    for payload in payloads:
                        response = session.get(endpoint,proxies=proxy,headers=header,params=payload)
                        response_handler(response,endpoint,payload)
                    payloads.clear()

                elif method == 'put' and action in ['sigin','sigup']:
                    payloads.append(xss_payloads)
                    data = {"username":payload,"email":"example@gmail.com","password":"Test@123:"}
                    for payload in payloads:
                        response = session.put(endpoint,proxies=proxy,headers=header,data=data)
                        response_handler(response,endpoint,payload)
                    payloads.clear()
                
                elif method == 'put' and action == 'login':
                    data = {"username": payload, "password": "Test@123:"}
                    payloads.append(xss_payloads)
                    for payload in payloads:
                        response = session.post(endpoint,proxies=proxy,headers=header,data=data)
                        response_handler(response,endpoint,payload)
                    #clearing the list after the scan for avoiding duplicate payloads
                    payloads.clear()
                
                elif method == 'put' and action not in ['login','sigin','sigup']:
                    payloads.append(xss_payloads)
                    for payload in payloads:
                        response = session.post(endpoint,proxies=proxy,headers=header,data=payload)
                        response_handler(response,endpoint,payload)
                        #clearing the list after the scan for avoiding duplicate payloads
                    payloads.clear()
                else:
                    sys.exit(1)

            elif sys.argv[2] == '-dir':
                if method == 'post' and action not in ['sigin','signup','login']:
                    payloads.append(dir_payloads)
                    for payload in payloads:
                        response = session.post(endpoint,proxies=proxy,headers=header,data=payload)
                        response_handler(response,endpoint,payload)
                    payloads.clear()

                elif method == 'get':
                    payloads.append(dir_payloads)
                    for payload in payloads:
                        response = session.get(endpoint,proxies=proxy,headers=header,params=payload)
                        response_handler(response,endpoint,payload)
                    payloads.clear()
                
                elif method == 'put' and action not in ['login','sigin','sigup']:
                    payloads.append(dir_payloads)
                    for payload in payloads:
                        response = session.post(endpoint,proxies=proxy,headers=header,data=payload)
                        response_handler(response,endpoint,payload)
                        #clearing the list after the scan for avoiding duplicate payloads
                    payloads.clear()
                else:
                    sys.exit(1)

            elif sys.argv[2] == '-ssrf':
                if method == 'post' and action not in ['sigin','signup','login']:
                    payloads.append(ssrf_payloads)
                    for payload in payloads:
                        response = session.post(endpoint,proxies=proxy,headers=header,data=payload)
                        response_handler(response,endpoint,payload)
                    payloads.clear()

                elif method == 'get':
                    payloads.append(ssrf_payloads)
                    for payload in payloads:
                        response = session.get(endpoint,proxies=proxy,headers=header,params=payload)
                        response_handler(response,endpoint,payload)
                    payloads.clear()
                
                elif method == 'put' and action not in ['login','sigin','sigup']:
                    payloads.append(ssrf_payloads)
                    for payload in payloads:
                        response = session.post(endpoint,proxies=proxy,headers=header,data=payload)
                        response_handler(response,endpoint,payload)
                        #clearing the list after the scan for avoiding duplicate payloads
                    payloads.clear()
                else:
                    sys.exit(1)
            else:
                print_help()
    
        except Exception as e:
            print(f"Check the url is correct {endpoint}: ", e)

def main():
    try:
        url = user_input()
        proxies = read_proxies()
        proxy = cycle(proxies)
        #cycle the proxies to make the all the request send through the proxies
        #using multi threading for make the code run litile bit faster
        for threads in range(6):
            thread = Thread(target=send_request,args=(next(proxy),url))
            thread.start()
        print("\nScanning for vulnerability..")
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()
