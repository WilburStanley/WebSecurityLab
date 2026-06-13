# Authentication Attack Scripts

## Vulnerability Context

**Type:** Username Enumeration  
**Category:** Information Disclosure / Improper Error Handling  
**OWASP:** A07:2021 Identification and Authentication Failures  
**CWE:** CWE-204 Observable Response Discrepancy

Applications that return subtly different error messages for invalid 
usernames vs invalid passwords unintentionally confirm the existence 
of accounts. The difference can be as subtle as a single character, 
a period, a space, or a capitalization difference, but is enough for 
automated tools to reliably distinguish valid from invalid usernames.

This is typically a human error during development, where different 
developers write different error messages, or copy paste 
inconsistencies appear across login form validation logic. A well 
designed authentication system should return a single, identical, 
generic error message regardless of which field failed validation.

## Overview
Two-phase attack: username enumeration followed by password brute force.
Both scripts use `ThreadPoolExecutor` to parallelize requests — significantly faster than sequential enumeration against large wordlists.

---

## Phase 1 — Username Enumeration via Different Responses
**Path:** `authentication/username-enumeration/response-text/username_enumeration.py`

Sends POST requests for each candidate username and parses the login form's warning message via BeautifulSoup. Compares each response against a baseline (known-invalid auth) — any deviation in the warning message leaks whether the username exists on the server.

### How It Works
1. Sends a baseline POST with dummy credentials to fingerprint a standard failed auth message
2. Iterates through the username wordlist, sending a POST per candidate with a constant dummy password
3. Parses the `<p class="is-warning">` element from each response
4. Flags any username whose warning message differs from the baseline

### Configuration
| Variable | Description |
|---|---|
| `url` | Target login endpoint |
| `wordlist_path` | Path to username wordlist |
| `num_of_workers` | Number of concurrent threads |
| `soup.find()` | **TODO: update tag and `class_` to match the target site's error element** |

---

## Phase 2 — Password Brute Force
**Path:** `authentication/password-bruteforce/basic/password_bruteforce.py`

Brute forces the password for a known valid username. Detects a successful auth via HTTP 302 redirect — the server redirects on valid credentials, returns a non-302 on failure.

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
- Username enumeration relies on the server returning a **different warning message** for a valid username vs an invalid one — not all login forms are vulnerable to this
- Password brute force relies on the server returning a **302 redirect** on successful auth — update the status code check if the target behaves differently

---

## Requirements
```bash
pip install requests beautifulsoup4
```