# SOC Command Center

> The operational brain behind Delta Force AI SOC — multi-agent system, automated log analysis, incident tracking, and Discord alerting.

---

## What This Is

The SOC Command Center is the local command and control layer of the Delta Force SOC platform. It runs the AI agent system, monitors incoming logs, escalates threats, and coordinates automated responses.

This connects directly to the Delta Force AI SOC Platform:
👉 [deltaforce-soc-ai](https://github.com/Romanm24/deltaforce-soc-ai)

---

## How It Works

Incoming log detected
→ auto_soc.py monitors log file
→ Threat analyzed by AI agents
→ Severity escalated based on attempt count
→ Incident report saved
→ Discord alert fired
→ Analyst action menu triggered

---

## Agent System

| Agent | Role |
|-------|------|
| `log_agent.md` | Analyzes authentication and system logs |
| `network_agent.md` | Analyzes traffic behavior and IP activity |
| `threat_agent.md` | Classifies severity and recommends response |
| `soc_orchestrator.md` | Coordinates all agents into one incident report |

---

## Key Files

| File | Purpose |
|------|---------|
| `auto_soc.py` | Monitors incoming logs and triggers analysis |
| `CLAUDE.md` | SOC AI agent instructions |
| `SOUL.md` | Agent identity and mindset |
| `INCIDENT_TEMPLATE.md` | Reusable incident analysis template |
| `SOC Log Analyzer.json` | n8n workflow export |
| `attacker_db.json` | Persistent attacker tracking database |
| `blocklist.txt` | IPs flagged for blocking |
| `investigated_logs.txt` | Logs marked as investigated |
| `reports/` | Timestamped incident reports |

---

## Analyst Action Menu

When a threat is detected the system presents:

--- SOC ACTION MENU ---

Run analysis again
Add another log manually
Mark this log as investigated
Prepare block-IP action
Block IP in Windows Firewall
Prepare Discord alert
Send Discord alert now
Save incident record
Save analyst notes template
Exit SOC tool

---

## Tech Stack

| Layer | Tool |
|-------|------|
| Agent System | VS Code + Claude Code |
| Automation | Python, n8n |
| AI Analysis | Claude AI (Anthropic) |
| Alerting | Discord webhooks |
| Tracking | JSON database, text logs |

---

## Project Status

- [x] Multi-agent SOC system
- [x] Automated log monitoring
- [x] Escalation logic
- [x] Discord alerting
- [x] Incident report generation
- [x] Analyst action menu
- [ ] Persistent IP tracking across sessions
- [ ] Dashboard UI
- [ ] Campus deployment

---

## Part of Delta Force SOC

This repo is the command center component of the larger Delta Force AI SOC Platform.

👉 [View the full platform](https://github.com/Romanm24/deltaforce-soc-ai)

---

**Built by Roman Mares — Cybersecurity student, SOC engineer, AI automation builder.**
