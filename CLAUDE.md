# CLAUDE.md — SOC Command Center (Agent System + Automation)

## Project Identity
- **Project:** Delta Force SOC Command Center
- **Company:** Delta Force Security LLC
- **Owner:** Roman Mares — Cybersecurity Engineer & AI SOC Builder
- **Email:** Roman.mares2012@gmail.com
- **This Repo:** `soc-command-center` — agent orchestration, automation logic, escalation pipelines
- **Main Platform Repo:** `deltaforce-soc-ai` — threat feed ingestion, D3.js dashboard, Claude classification pipeline

---

## What This Repo Is
This is the **agent system and automation layer** of the Delta Force AI SOC — not the threat intelligence platform.

Responsibilities of this repo:
- **Multi-agent orchestration** — Claude Code agents (orchestrator + specialists) analyzing raw logs
- **Automated log triage** — `auto_soc.py` polls `incoming_logs.txt`, builds Claude prompts, fires the agent pipeline
- **Analyst action menu** — interactive CLI for marking logs investigated, IP blocking, Discord dispatch
- **Incident report generation** — structured reports saved under `reports/`
- **Discord alerting** — direct webhook dispatch from Python (not through n8n) for this command center
- **n8n workflow exports** — workflow JSON files for automation flows built in this context

---

## Tech Stack
| Layer | Tools |
|---|---|
| Agent Orchestration | Claude Code agents (`.md` definitions) |
| AI Backend | Claude AI — `claude-sonnet-4-6` |
| Automation Script | Python 3.10+ (`auto_soc.py`) |
| Log Ingestion | File-based (`incoming_logs.txt`) |
| Alerting | Discord webhooks (direct Python HTTP) |
| Workflow Exports | n8n JSON |
| Response Actions | Windows Firewall (`netsh`), blocklist file |
| Env Management | `python-dotenv` |

---

## Agent Architecture

Four Claude Code agents work in a fixed pipeline. All agent definitions live in `agents/`.

```
incoming_logs.txt
      ↓
auto_soc.py  →  builds prompt  →  soc_orchestrator
                                        ↓
                           ┌────────────┼────────────┐
                      log_agent   network_agent  threat_agent
                           └────────────┼────────────┘
                                        ↓
                               SOC Incident Report
                                        ↓
                          reports/incident_<timestamp>.txt
```

### Agent Roles

| Agent | File | Responsibility |
|---|---|---|
| `soc_orchestrator` | `agents/soc_orchestrator.md` | Coordinates the three sub-agents; owns final incident report format |
| `log_agent` | `agents/log_agent.md` | SSH failures, login anomalies, brute force detection |
| `network_agent` | `agents/network_agent.md` | IP behavior, internal vs. external traffic, suspicious connections |
| `threat_agent` | `agents/threat_agent.md` | Severity classification, MITRE ATT&CK mapping, response recommendations |

### Incident Report Format (enforced by soc_orchestrator)
```
# SOC Incident Report

## 1. Event Summary
## 2. Log Analysis       (log_agent output)
## 3. Network Analysis   (network_agent output)
## 4. Threat Classification  (threat_agent output — includes MITRE mapping)
## 5. Recommended Actions   (Immediate / Short-term / Long-term)
## 6. Analyst Bottom Line   (one decision statement)
```

### Escalation Rules (soc_orchestrator)
- Escalate on repeated SSH failures, invalid user attempts, or lateral movement indicators
- Treat internal-origin brute force as high concern regardless of volume
- If evidence is incomplete, document what is known and flag gaps — do not guess

---

## Core Automation Script — `auto_soc.py`

`auto_soc.py` is the central automation engine. It polls `incoming_logs.txt` every 3 seconds for new lines and drives the full triage workflow.

### Log Processing Flow
```
New line in incoming_logs.txt
  → extract_source_ip()       # parse "from <ip>" token
  → extract_protocol()        # detect SSH / RDP / HTTP
  → infer_internal_or_external()  # RFC 1918 check
  → build_prompt()            # construct soc_orchestrator prompt
  → save_latest_prompt()      # write to latest_incident_prompt.txt
  → save_incident_report()    # write to reports/incident_<ts>.txt
  → soc_menu()                # interactive analyst action menu
```

### SOC Action Menu Options
| Option | Action |
|---|---|
| 1 | Re-run analysis (rebuild prompt) |
| 2 | Add another log manually |
| 3 | Mark log as investigated → `investigated_logs.txt` |
| 4 | Prepare block-IP entry → `blocklist.txt` |
| 5 | Block IP in Windows Firewall (`netsh advfirewall`) |
| 6 | Save Discord alert to file |
| 7 | Send Discord alert via webhook |
| 8 | Save another incident record copy |
| 9 | Save analyst notes template |
| 10 | Exit |

---

## Discord Webhook Alerting

Discord alerts in this repo are dispatched directly from Python using `urllib.request` (no n8n intermediary).

### Alert Payload (plain text, code block format)
```
SOC ALERT
Time: <ISO 8601>
Event: Suspicious authentication activity detected
Source IP: <ip>
Protocol: <protocol>
Log: <raw log line>
Recommended Action: Review incident, validate severity, and investigate host behavior.
```

### Severity-to-Color Reference (for embed-based alerts)
| Severity | Decimal Color |
|---|---|
| CRITICAL | `16711680` (red) |
| HIGH | `16744272` (orange) |
| MEDIUM | `16776960` (yellow) |
| LOW | `65280` (green) |

### Webhook URL
- Loaded from `DISCORD_WEBHOOK_URL` environment variable — never hardcoded in source
- Set in `.env`, never committed

---

## n8n Workflow Design (Exports in This Repo)

Workflow JSON files (e.g., `SOC Log Analyzer.json`) represent n8n workflows scoped to this command center layer — log analysis routing, escalation triggers, and analyst notification flows.

### Design Rules
- Each workflow does **one thing** — single-purpose only
- Every node must have an **error branch**
- Use **Set nodes** to normalize data between nodes
- Validate webhook payloads before processing
- Node naming convention: `[ACTION] — [DESCRIPTION]` (e.g., `HTTP — Post Discord Alert`)

### Standard Escalation Workflow Pattern
```
[Trigger] → [Validate] → [Set — Normalize Log] → [Claude — Orchestrate] → [Set — Format Alert] → [Discord — Send]
                                                                                                  ↓ (on error)
                                                                                        [Discord — Send Error]
```

---

## File Structure
```
soc-command-center/
├── CLAUDE.md                    ← You are here
├── SOUL.md                      ← System identity / analyst persona
├── INCIDENT_TEMPLATE.md         ← Standard incident documentation template
├── auto_soc.py                  ← Core automation engine (log monitor + action menu)
├── discord_test.py              ← Discord webhook smoke test
├── attacker_db.json             ← Tracked attacker/IOC records
├── incoming_logs.txt            ← Live log ingestion file (append new events here)
├── investigated_logs.txt        ← Archive of triaged log lines
├── blocklist.txt                ← IPs flagged for blocking
├── latest_incident_prompt.txt   ← Last generated Claude prompt (for debugging)
├── agents/
│   ├── soc_orchestrator.md      ← Orchestrator agent definition
│   ├── log_agent.md             ← Log analysis agent
│   ├── network_agent.md         ← Network traffic agent
│   └── threat_agent.md          ← Threat classification agent
├── reports/                     ← Auto-generated incident records
│   └── incident_<timestamp>.txt
├── SOC Log Analyzer.json        ← n8n workflow export
└── screenshots/                 ← Documentation screenshots
```

---

## Environment Variables
All secrets loaded from `.env` — never hardcoded.

| Variable | Purpose |
|---|---|
| `DISCORD_WEBHOOK_URL` | Discord alert channel for this command center |
| `ANTHROPIC_API_KEY` | Claude AI API (if used directly in Python scripts) |
| `N8N_WEBHOOK_SECRET` | Validates inbound n8n triggers |
| `LOG_LEVEL` | Logging verbosity (`INFO` / `DEBUG`) |

---

## Coding Standards

### General
- All code must be **modular** — no monolithic functions, keep concerns separated
- Every Python script must use the `logging` module — never `print()` for operational output
- All secrets via environment variables — no hardcoded URLs, keys, or tokens
- Error handling on every external call: Discord webhooks, subprocess commands, file I/O

### Python
- Python 3.10+ syntax
- Use `python-dotenv` for `.env` loading
- Follow PEP8
- Prefer `requests` for HTTP; `aiohttp` for async pipelines
- Add docstrings to all functions
- Log at `INFO` for normal flow, `ERROR` for failures, `DEBUG` for raw data

### Agent Definitions (`.md` files in `agents/`)
- Define **role, focus areas, and output format** only — no implementation logic
- Keep agent prompts concise and deterministic
- Orchestrator owns the final report format — sub-agents return structured summaries only
- Never embed API keys or external URLs in agent definition files

---

## MITRE ATT&CK Standards
All threat classifications from `threat_agent` must map to a MITRE tactic and technique.

```
Tactic: <TA####> — <Tactic Name>
Technique: <T####> — <Technique Name>
Confidence: HIGH / MEDIUM / LOW
```

### Quick Reference
| Threat Type | Tactic | Technique |
|---|---|---|
| SSH Brute Force | TA0006 — Credential Access | T1110 — Brute Force |
| Phishing | TA0001 — Initial Access | T1566 — Phishing |
| C2 Beacon | TA0011 — Command & Control | T1071 — App Layer Protocol |
| Credential Dump | TA0006 — Credential Access | T1003 — OS Credential Dumping |
| Lateral Movement | TA0008 — Lateral Movement | T1021 — Remote Services |
| Data Exfil | TA0010 — Exfiltration | T1041 — Exfil Over C2 Channel |

---

## What Claude Code Should NOT Do
- Never hardcode `DISCORD_WEBHOOK_URL` or any token in source files — always load from `.env`
- Never use `print()` for logging — use the `logging` module
- Never commit `.env`, `blocklist.txt` contents with real IPs, or `attacker_db.json` with sensitive IOCs
- Never skip error handling on `subprocess` calls (firewall rules) or `urllib` calls (Discord)
- Never create a single-file monolith — keep `auto_soc.py` functions small and focused
- Never modify `investigated_logs.txt` or `reports/` entries retroactively — these are append-only audit records
- Never set Claude `temperature` above `0.3` for threat classification tasks
- Never add logic to agent `.md` files — they are prompt definitions, not code

---

## Current Build Priorities
1. Harden `auto_soc.py` — move hardcoded webhook URL to `.env`, replace `print()` with `logging`
2. Expand `threat_agent` with full MITRE technique coverage for SSH/RDP brute force
3. Build escalation workflow — auto-escalate CRITICAL findings to Discord without analyst menu interaction
4. Enrich `attacker_db.json` with IOC lookups (AbuseIPDB, OTX) for known attacker IPs
5. Campus cyber lab pilot — deploy command center on a monitored lab segment
