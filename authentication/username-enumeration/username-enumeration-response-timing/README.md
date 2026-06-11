# Authentication Attack Script

## Overview

Single-script attack: timing-based username enumeration with built-in threshold
calibration and multi-round verification.

Uses sequential requests with spoofed `X-Forwarded-For` headers to bypass
IP-based rate limiting.

---

## Baseline : Fingerprinting the Fast Path

Sends a single request with a guaranteed-invalid username to measure the
server's fast-path response time — the time it takes when no bcrypt hashing
occurs. This becomes the lower reference point for threshold calculation.

---

## Calibration : Measuring Real bcrypt Time

Probes a known-valid username across multiple rounds to measure real bcrypt
response time on the target. Uses both measurements to calculate a dynamic
flag threshold:

```
threshold = baseline + (CALIBRATION_MARGIN * (known_valid_avg - baseline))
```

With `CALIBRATION_MARGIN = 0.5`, the threshold sits halfway between the
baseline and the known-valid average — wide enough to catch valid usernames,
strict enough to filter noise.

If the gap between baseline and calibration is less than `0.5s`, the script
will warn that the target may be under load or not using a slow hashing
algorithm — consider re-running or lowering `CALIBRATION_MARGIN`.

---

## Phase 1 : Username Enumeration

**Path:** `authentication/username-enumeration/username_enumeration_via_response_timing.py`

Targets a faulty design where the server takes longer to respond for valid
usernames due to bcrypt password hashing. When a username exists, the server
runs the full bcrypt comparison regardless of whether the password is correct.
When a username does not exist, the server short-circuits before hashing
entirely. The timing difference between these two paths leaks whether a
username is recognized.

A long dummy password (`"A" * 200`) is used to exaggerate the bcrypt
computation time and widen the gap between valid and invalid responses.

### How It Works

1. Iterates through the username wordlist, sending a POST per candidate
2. Measures `response.elapsed` (server-side processing time) for each request
3. Spoofs a fresh random IP via `X-Forwarded-For` on every request to bypass rate limiting
4. Flags any candidate whose response time exceeds the calibrated threshold
5. Prints both `Response Received` (server time) and `Response Completed` (total round-trip) per result

### Configuration

| Variable | Description |
|---|---|
| `URL` | Target login endpoint |
| `WORDLIST` | Path to username wordlist |
| `PASSWORD` | Long dummy password to exaggerate bcrypt timing |
| `BASELINE_USERNAME` | Guaranteed-invalid username for baseline measurement |
| `CALIBRATION_USERNAME` | **TODO: update to a confirmed valid username on the target** |
| `CALIBRATION_ROUNDS` | Number of rounds to probe the known-valid username |
| `CALIBRATION_MARGIN` | Fraction of the calibration gap used to set the threshold — lower = more sensitive, higher = stricter |
| `MAX_RETRIES` | Retries on connection error before skipping a username — applies globally across baseline, calibration, and enumeration |
| `RETRY_DELAY` | Seconds to wait between retries — applies globally across baseline, calibration, and enumeration |

---

## Phase 2 : Candidate Verification

Re-tests each flagged username across `VERIFY_ROUNDS` rounds. A username is
confirmed only if it beats the threshold in the majority of rounds (`> 50%`)
— this filters out one-off jitter false positives from Phase 1.

Confirmed usernames are reported with their average response time and hit
count. Rejected candidates are noted as inconsistent timing.

## Phase 3 : Password Brute Force

**Path:** `authentication/username-enumeration/password_bruteforce_basic_ip_protection.py`

Using the confirmed username from Phase 2, brute forces the login form by
iterating through a password wordlist. Uses `ThreadPoolExecutor` to parallelize
requests, significantly faster than sequential brute force against large wordlists.

Detects a successful auth via HTTP 302 redirect — the server redirects on valid
credentials, returns 200 on failure. Stops immediately once a 302 is found and
cancels remaining threads.

### How It Works

1. Iterates through the password wordlist concurrently across multiple threads
2. Sends each request with `allow_redirects=False` to intercept the raw status code before any redirect is followed
3. Spoofs a deterministic IP per password index via `X-Forwarded-For` — reproducible across runs
4. Flags a 302 as a successful auth hit and terminates remaining threads immediately

### Configuration

| Variable | Description |
|---|---|
| `VERIFY_ROUNDS` | Number of re-test rounds per flagged candidate |

---

## Assumptions & Limitations

- Wordlist must contain the valid username, otherwise the script will not find a hit
- Login form fields must be named `username` and `password` — update `data={}` if not
- Enumeration relies on the server using a **slow hashing algorithm** (e.g. bcrypt) — targets without it will show no meaningful timing gap
- Rate limiting must be bypassable via `X-Forwarded-For` — update or remove the spoofed headers if the target uses a different mechanism
- A known-valid username is required upfront for calibration — `wiener` is the default for PortSwigger labs

---

## Requirements

```bash
pip install requests
```