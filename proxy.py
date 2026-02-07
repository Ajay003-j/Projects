import time,os,requests

def get_proxies():
    while True:
        proxy = None
        try:
            time.sleep(5)  # slow down to avoid rate limit
            response = requests.get("http://pubproxy.com/api/proxy?level=elite", timeout=5)

            # Only parse JSON if status is 200 and body is not empty
            if response.status_code == 200 and response.text.strip():
                data = response.json()
                # Extract fields
                proxy_ip_port = data['data'][0]['ipPort']
                proxy_protocol = data['data'][0]['type'].lower()
                proxy = f"{proxy_protocol}://{proxy_ip_port}"
            else:
                time.sleep(10)
                return 1
        except Exception as e:
            time.sleep(10)
            return 1

        # Skip if proxy wasn't set
        if proxy is None:
            continue

        # Ensure file exists
        if not os.path.exists("proxy.txt"):
            open("proxy.txt", "w").close()

        with open("proxy.txt", "r") as p:
            exists = p.read().splitlines()
        #Ensure the proxy dose not already exits and write it in a file
        if proxy in exists:
            continue
        else:
            try:
                with open("proxy.txt", "a") as f:
                    f.write(proxy + "\n")
            except Exception as e:
                print(e)
            