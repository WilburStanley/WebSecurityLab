# Password Brute Force : Basic

**Path:** `authentication/password-bruteforce/basic/password_bruteforce.py`

Brute forces the password for a known valid username. Detects a successful auth via HTTP 302 redirect — the server redirects on valid credentials, returns a non-302 on failure.

## Vulnerability Context

**Type:** Password Brute Force  
**Category:** Broken Authentication / Missing Brute Force Protection  
**OWASP:** A07:2021 Identification and Authentication Failures  
**CWE:** CWE-307 Improper Restriction of Excessive Authentication Attempts

Applications that impose no limit on authentication attempts allow
attackers to systematically guess passwords without any friction or
consequence. With no lockout mechanism, rate limiting, or CAPTCHA in
place, the only barrier between an attacker and a valid account is
the size of the password wordlist and the speed of the connection.

This is the most straightforward authentication weakness, the
application simply has no defense against repeated login attempts.
A well designed authentication system should implement account lockout,
progressive delays, or anomaly detection to restrict excessive
authentication attempts.

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