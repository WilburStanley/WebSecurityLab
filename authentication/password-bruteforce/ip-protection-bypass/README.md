# Password Brute Force — IP Protection Bypass

**Path:** `authentication/password-bruteforce/ip-protection-bypass/password_bruteforce.py`

Brute forces the password for a known valid username against a target that enforces IP based lockout. Bypasses the lockout by spoofing a different public IP on every request via proxy headers — the server trusts these headers to identify the client, making the lockout trivially bypassable.

## Usage

Run this script after completing Phase 1 (username enumeration). Update `VALID_USERNAME` with the result before running.

Applicable after:
- `authentication/username-enumeration/response-text/username_enumeration.py`
- `authentication/username-enumeration/response-length/username_enumeration.py`
- `authentication/username-enumeration/response-timing/username_enumeration.py`

## How It Works

1. Generates a unique public IP per password attempt using a seeded RNG — deterministic and reproducible
2. Injects the spoofed IP into `X-Forwarded-For`, `X-Real-IP`, `X-Remote-IP`, and `X-Client-IP` headers
3. Sends concurrent POST requests via `ThreadPoolExecutor` — safe here since order does not matter
4. Each request uses `allow_redirects=False` to intercept the raw status code
5. Retries up to 3 times on connection errors before skipping
6. Flags a 302 as a successful auth hit and terminates remaining threads immediately

## Why This Works

The server uses the client IP to track failed attempts but derives that IP from proxy headers instead of the actual TCP connection. Since these headers are user controlled, a different spoofed IP per request means the server sees each attempt as coming from a new client — the lockout counter never accumulates.

## Configuration

| Variable | Description |
|---|---|
| `URL` | Target login endpoint |
| `WORDLIST` | Path to password wordlist |
| `VALID_USERNAME` | **TODO: update from Phase 1 enumeration results** |
| `NUM_WORKERS` | Number of concurrent threads |

## Assumptions & Limitations

- Wordlist must contain the valid password, otherwise the script will not find a hit
- Login form fields must be named `username` and `password` — update `data={}` if not
- Relies on the server returning a **302 redirect** on successful auth — update the status code check if the target behaves differently
- Only effective if the target trusts at least one of the spoofed headers to identify the client IP — if the server uses the actual TCP source IP, this bypass will not work

## Requirements

```bash
pip install requests
```