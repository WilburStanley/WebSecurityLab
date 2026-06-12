# Password Brute Force — Flawed Lockout Bypass

**Path:** `authentication/password-bruteforce/flawed-lockout-bypass/password_bruteforce.py`

Brute forces the password for a known valid username against a target with a flawed lockout mechanism. The server resets the failed attempt counter on any successful login — regardless of which account logged in. This script exploits that flaw by interleaving valid credentials every N attempts to keep the counter from ever reaching the lockout threshold.

## Vulnerability

This attack targets a **broken brute force protection** implementation where the lockout counter is not isolated per account. A successful login from any account resets the counter globally or per session, meaning an attacker can continuously reset it by authenticating with a known valid account between guesses.

This is a business logic flaw — the lockout mechanism exists but its reset condition is too broad, making it trivially bypassable without any IP spoofing or header manipulation.

## Why Sequential Execution

Threading is intentionally skipped for this script. The attack depends on a strict request order:

```
Attempt 1  : target_username : password_guess_1
Attempt 2  : target_username : password_guess_2
Reset      : valid_username  : valid_password     # resets the counter
Attempt 3  : target_username : password_guess_3
Attempt 4  : target_username : password_guess_4
Reset      : valid_username  : valid_password     # resets again
```

The reset must reach the server before the lockout threshold is hit. Concurrent threads cannot guarantee server side arrival order — a reset that fires out of sequence either resets too early (wasting a slot) or too late (triggering lockout). Sequential execution is the only way to guarantee the reset fires at the right time every time.

## Usage

This script is standalone. Unlike the other brute force scripts, it does not require a prior enumeration phase path — it only requires a known valid username for the target account and a separate valid account to use as the reset credential.

Update the config block before running:
- `TARGET_USERNAME` with the account to brute force
- `RESET_USERNAME` and `RESET_PASSWORD` with any valid credentials on the same application
- `LOCKOUT_THRESHOLD` to match the target's allowed attempts before lockout

## How It Works

1. Loads the password wordlist and iterates sequentially — no threading
2. Every `LOCKOUT_THRESHOLD` attempts, sends a login with the reset credentials first
3. A successful reset login resets the server side failed attempt counter
4. Sends the next password guess immediately after the reset
5. Uses `allow_redirects=False` to intercept the raw status code
6. Flags a 302 as a successful auth hit and stops immediately

## Configuration

| Variable | Description |
|---|---|
| `URL` | Target login endpoint |
| `WORDLIST` | Path to password wordlist |
| `TARGET_USERNAME` | Account to brute force |
| `RESET_USERNAME` | Valid account used to reset the lockout counter |
| `RESET_PASSWORD` | Password for the reset account |
| `LOCKOUT_THRESHOLD` | **TODO: update if the target has a different threshold** |

## Assumptions & Limitations

- Wordlist must contain the valid password, otherwise the script will not find a hit
- Login form fields must be named `username` and `password` — update `data={}` if not
- Relies on the server returning a 302 redirect on successful auth — update the status code check if the target behaves differently
- Only effective if the server resets the lockout counter on any successful login — if the counter is isolated per account this bypass will not work
- `LOCKOUT_THRESHOLD` must be set correctly — too high and the script will trigger lockout before the reset fires

## Requirements

```bash
pip install requests
```