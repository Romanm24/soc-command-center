import json
import urllib.request
import urllib.error

WEBHOOK_URL = "import logging
import time
import os
import json
import urllib.request
import urllib.error
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(message)s",
)

LOG_FILE = "incoming_logs.txt"
PROMPT_FILE = "latest_incident_prompt.txt"
REPORTS_DIR = "reports"
INVESTIGATED_FILE = "investigated_logs.txt"
BLOCKLIST_FILE = "blocklist.txt"
DISCORD_ALERT_FILE = "latest_discord_alert.txt"

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")


def ensure_files():
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, "w", encoding="utf-8").close()

    if not os.path.exists(INVESTIGATED_FILE):
        open(INVESTIGATED_FILE, "w", encoding="utf-8").close()

    if not os.path.exists(BLOCKLIST_FILE):
        open(BLOCKLIST_FILE, "w", encoding="utf-8").close()

    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)


def read_new_logs(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.readlines()


def extract_source_ip(log: str) -> str:
    parts = log.split()
    for i, token in enumerate(parts):
        if token.lower() == "from" and i + 1 < len(parts):
            return parts[i + 1]
    return "Unknown"


def extract_protocol(log: str) -> str:
    lower = log.lower()
    if "ssh" in lower:
        return "SSH"
    if "rdp" in lower:
        return "RDP"
    if "http" in lower or "https" in lower:
        return "HTTP/HTTPS"
    return "Unknown"


def infer_internal_or_external(ip: str) -> str:
    if ip.startswith("10.") or ip.startswith("192.168.") or ip.startswith("172.16.") or ip.startswith("172.17.") or ip.startswith("172.18.") or ip.startswith("172.19.") or ip.startswith("172.2") or ip.startswith("172.30.") or ip.startswith("172.31."):
        return "Internal"
    return "Unknown/External"


def build_prompt(log: str) -> str:
    source_ip = extract_source_ip(log)
    protocol = extract_protocol(log)
    boundary = infer_internal_or_external(source_ip)

    return f"""Use soc_orchestrator:

Analyze this event:

{log}

Context:
- Source IP: {source_ip}
- Destination IP: Unknown
- Protocol: {protocol}
- Repeated attempts: Unknown
- Internal or external: {boundary}
- Notes: Auto-detected log

Return a full SOC incident report.
"""


def save_latest_prompt(prompt: str):
    with open(PROMPT_FILE, "w", encoding="utf-8") as f:
        f.write(prompt)


def save_incident_report(log: str, prompt: str):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(REPORTS_DIR, f"incident_{timestamp}.txt")

    contents = f"""SOC INCIDENT RECORD
Timestamp: {datetime.now().isoformat()}

Log:
{log}

Generated Prompt:
{prompt}
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(contents)

    logging.info("Incident record saved: %s", filename)


def mark_investigated(log: str):
    with open(INVESTIGATED_FILE, "a", encoding="utf-8") as f:
        f.write(log + "\n")
    logging.info("Log marked as investigated.")


def prepare_block_ip(log: str):
    source_ip = extract_source_ip(log)

    if source_ip == "Unknown":
        logging.warning("Could not find a source IP to add to blocklist.")
        return

    with open(BLOCKLIST_FILE, "a", encoding="utf-8") as f:
        f.write(source_ip + "\n")

    logging.info("Added to blocklist file: %s", source_ip)
    logging.info("Review before enforcing on a firewall.")


def block_ip_windows_firewall(log: str):
    source_ip = extract_source_ip(log)

    if source_ip == "Unknown":
        logging.warning("Could not find a source IP to block.")
        return

    confirm = input(f"Block {source_ip} in Windows Firewall now? (yes/no): ").strip().lower()
    if confirm != "yes":
        logging.info("Firewall block cancelled.")
        return

    rule_name = f"SOC_Block_{source_ip}"
    cmd = [
        "netsh", "advfirewall", "firewall", "add", "rule",
        f"name={rule_name}",
        "dir=in",
        "action=block",
        f"remoteip={source_ip}"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logging.info("Firewall rule created successfully.")
        logging.debug(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        logging.error("Failed to create firewall rule.")
        if e.stdout:
            logging.debug(e.stdout.strip())
        if e.stderr:
            logging.error(e.stderr.strip())


def build_discord_alert(log: str) -> str:
    source_ip = extract_source_ip(log)
    protocol = extract_protocol(log)

    return f"""SOC ALERT
Time: {datetime.now().isoformat()}
Event: Suspicious authentication activity detected
Source IP: {source_ip}
Protocol: {protocol}
Log: {log}
Recommended Action: Review incident, validate severity, and investigate host behavior.
"""


def prepare_discord_alert(log: str):
    alert = build_discord_alert(log)

    with open(DISCORD_ALERT_FILE, "w", encoding="utf-8") as f:
        f.write(alert)

    logging.info("Discord alert content saved to: %s", DISCORD_ALERT_FILE)


def send_discord_alert(log: str):
    if not DISCORD_WEBHOOK_URL.strip():
        logging.error("DISCORD_WEBHOOK_URL is not set. Add it to .env.")
        return

    alert = build_discord_alert(log)

    payload = {"content": f"```{alert}```"}
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        DISCORD_WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as response:
            logging.info("Discord alert sent. HTTP %s", response.status)
    except urllib.error.HTTPError as e:
        logging.error("Discord webhook failed. HTTP %s", e.code)
    except urllib.error.URLError as e:
        logging.error("Discord webhook connection failed: %s", e.reason)


def save_analyst_notes(log: str):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(REPORTS_DIR, f"analyst_notes_{timestamp}.txt")

    source_ip = extract_source_ip(log)
    protocol = extract_protocol(log)

    template = f"""SOC ANALYST NOTES
Timestamp: {datetime.now().isoformat()}

Event Summary:
- Suspicious event detected from source IP {source_ip}
- Protocol: {protocol}
- Original log: {log}

Initial Triage:
- Severity:
- Confirmed repeated attempts:
- Internal or external:
- User/account targeted:
- Systems affected:

Containment Actions:
- Host isolated:
- IP blocked:
- Firewall rule added:
- EDR check performed:

Investigation Notes:
- Successful login observed:
- Lateral movement indicators:
- Additional logs reviewed:
- PCAP reviewed:
- Malware/process findings:

Final Disposition:
- True positive / False positive:
- Escalated to IR:
- Remediation completed:
- Follow-up required:
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(template)

    logging.info("Analyst notes template saved: %s", filename)


def process_log(log: str):
    prompt = build_prompt(log)

    logging.info("SOC ANALYSIS REQUEST")
    logging.debug(prompt)

    save_latest_prompt(prompt)
    save_incident_report(log, prompt)
    soc_menu(log, prompt)


def soc_menu(log: str, prompt: str):
    while True:
        print("\n--- SOC ACTION MENU ---")
        print("1. Run analysis again")
        print("2. Add another log manually")
        print("3. Mark this log as investigated")
        print("4. Prepare block-IP action")
        print("5. Block IP in Windows Firewall now")
        print("6. Prepare Discord alert file")
        print("7. Send Discord alert now")
        print("8. Save another incident record copy")
        print("9. Save analyst notes template")
        print("10. Exit SOC tool")

        choice = input("Select an option: ").strip()

        if choice == "1":
            logging.info("Rebuilding analysis prompt.")
            save_latest_prompt(prompt)
            logging.debug(prompt)

        elif choice == "2":
            new_log = input("Enter new log: ").strip()
            if new_log:
                process_log(new_log)
                return
            print("No log entered.")

        elif choice == "3":
            mark_investigated(log)
            return

        elif choice == "4":
            prepare_block_ip(log)

        elif choice == "5":
            block_ip_windows_firewall(log)

        elif choice == "6":
            prepare_discord_alert(log)

        elif choice == "7":
            send_discord_alert(log)

        elif choice == "8":
            save_incident_report(log, prompt)

        elif choice == "9":
            save_analyst_notes(log)

        elif choice == "10":
            print("Exiting SOC tool...")
            raise SystemExit

        else:
            print("Invalid option. Try again.")


def main():
    ensure_files()

    logging.info("Monitoring logs...")
    seen = set()

    while True:
        logs = read_new_logs(LOG_FILE)

        for log in logs:
            clean_log = log.strip()

            if clean_log and clean_log not in seen:
                seen.add(clean_log)
                process_log(clean_log)

        time.sleep(3)


if __name__ == "__main__":
    main() "

payload = {
    "content": "SOC test message from Python"
}

data = json.dumps(payload).encode("utf-8")

req = urllib.request.Request(
    WEBHOOK_URL,
    data=data,
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req) as response:
        print(f"Success. HTTP {response.status}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    try:
        print(e.read().decode("utf-8", errors="ignore"))
    except:
        pass
except urllib.error.URLError as e:
    print(f"URL Error: {e.reason}")
