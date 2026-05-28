# SmartPN Atlas ??Automation Details
Version: v1.0 | 2026-05-28

## Automation Status Table
| ID | Name | Status | Tool |
|----|------|--------|------|
| A1 | LinkedIn Interaction Radar | VERIFY | Codex toml exists |
| A2 | LinkedIn Workflow Check-in | VERIFY | Codex toml exists |
| A3 | Website Deploy Monitor | VERIFY | Codex toml exists |
| A4 | LinkedIn Publish Pipeline | TODO | Make + Claude API |
| A5 | LinkedIn Reply Automation | TODO | Make + LinkedIn API |
| A6 | LinkedIn x Website Sync | TODO | Make + Netlify |
| A7 | n8n Approval Queue | TODO | n8n |
| A8 | SaaS Demo Builder baseline | VERIFY | docs/preview/saas_demo_autonomous/index.html |
| A9 | SaaS Demo Patch Improver | TODO | Codex low-token patch |

## Codex Automation Paths
C:\Users\user\.codex\automations\smartpn-linkedin-interaction-radar\automation.toml
C:\Users\user\.codex\automations\smartpn-linkedin-workflow-check-in\automation.toml
C:\Users\user\.codex\automations\smartpn-website-deploy-recovery-monitor\automation.toml

## Daily Report Output
D:\SmartPN_Atlas_Workspace\03_Outputs\Automation_Daily_Reports\
Format: YYYY-MM-DD_smartpn_daily_report.md

## Iron Rules
- Never auto-publish LinkedIn content
- Never deploy website without Jim approval
- Never claim automation works unless verified
- LinkedIn radar: individuals only, no company pages

## Tool Layer Design
| Layer | Tool | Responsibility |
|-------|------|----------------|
| Thinking | Claude | Scenario design, JSON, HTML, articles |
| Backup | Gemini | Cross-check only (summary-level memory) |
| Code | Codex/GPT | Demo software, automation scripts |
| Execution | Make/n8n | Triggers, schedules, API connections |
| Version Control | GitHub | Single source of truth |
| Deploy | Netlify | Auto-deploy from main branch |
