import json
import urllib.request
import urllib.error

WEBHOOK_URL = "https://discord.com/api/webhooks/1495660209601777775/ipVZRylgoIQa7oafbfb1AMfiYvRAP5BkL-IODtSwJvbMmq3hBPyz7AczI8P3b2c-aTwt"

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