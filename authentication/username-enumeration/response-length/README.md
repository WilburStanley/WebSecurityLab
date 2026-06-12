# Authentication Attack Scripts

## Overview
Two-phase attack: username enumeration followed by password brute force.
Both scripts use `ThreadPoolExecutor` to parallelize requests, significantly faster than sequential enumeration against large wordlists.

---

## Phase 1 : Username Enumeration via Response Length
**Path:** `authentication/username-enumeration/response-length/username_enumeration.py`

Targets a faulty design where the server returns a different response length depending on whether a username exists or not. The difference in response length leaks whether the username is recognized — we use this to enumerate valid usernames.

### How It Works
1. Sends a baseline POST with dummy credentials to fingerprint the response length of a guaranteed failed auth
2. Iterates through the username wordlist, sending a POST per candidate with a constant dummy password
3. Measures the response length of each request
4. Flags any username whose response length deviates from the baseline

### Configuration
| Variable | Description |
|---|---|
| `url` | Target login endpoint |
| `wordlist_path` | Path to username wordlist |
| `num_of_workers` | Number of concurrent threads |

---

## Phase 2 : Password Brute Force
**Path:** `authentication/password-bruteforce/basic/password_bruteforce.py`

Using the viable username found from Phase 1, brute forces the login form by iterating through a password wordlist. Detects a successful auth via HTTP 302 redirect — the server redirects on valid credentials, returns a non-302 on failure.

### How It Works
1. Iterates through the password wordlist, sending a POST per candidate against the known username
2. Sends each request with `allow_redirects=False` to intercept the raw status code
3. Flags a 302 as a successful auth hit and terminates remaining threads immediately

### Configuration
| Variable | Description |
|---|---|
| `url` | Target login endpoint |
| `wordlist_path` | Path to password wordlist |
| `known_username` | **TODO: update from Phase 1 enumeration results** |
| `num_of_workers` | Number of concurrent threads |

---

## Assumptions & Limitations
- Wordlists must contain the valid username/password, otherwise the scripts will not find a hit
- Login form fields must be named `username` and `password` — update `data={}` in the scripts if not
- Username enumeration relies on the server returning a **different response length** for a valid username vs an invalid one — not all login forms are vulnerable to this
- Password brute force relies on the server returning a **302 redirect** on successful auth — update the status code check if the target behaves differently

---

## Requirements
```bash
pip install requests
```