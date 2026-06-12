# Password Brute Force — Basic

**Path:** `authentication/password-bruteforce/basic/password_bruteforce.py`

Brute forces the password for a known valid username. Detects a successful auth via HTTP 302 redirect — the server redirects on valid credentials, returns a non-302 on failure.

---

## Usage

Run this script after completing Phase 1 (username enumeration). Update `known_username` with the result before running.

Applicable after:
- `authentication/username-enumeration/response-text/username_enumeration.py`
- `authentication/username-enumeration/response-length/username_enumeration.py`

---

## How It Works

1. Loads the password wordlist and spawns concurrent threads via `ThreadPoolExecutor`
2. Sends a POST request per password candidate against the known username
3. Each request uses `allow_redirects=False` to intercept the raw status code
4. Flags a 302 as a successful auth hit and terminates remaining threads immediately

---

## Configuration

| Variable | Description |
|---|---|
| `url` | Target login endpoint |
| `wordlist_path` | Path to password wordlist |
| `known_username` | **TODO: update from Phase 1 enumeration results** |
| `num_of_workers` | Number of concurrent threads |

---

## Assumptions & Limitations

- Wordlist must contain the valid password, otherwise the script will not find a hit
- Login form fields must be named `username` and `password` — update `data={}` if not
- Relies on the server returning a **302 redirect** on successful auth — update the status code check if the target behaves differently
- No brute force protection assumed — use `authentication/password-bruteforce/flawed-lockout-bypass/` if the target has a lockout mechanism

---

## Requirements

```bash
pip install requests
```