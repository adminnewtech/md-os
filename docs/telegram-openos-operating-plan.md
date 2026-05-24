# OPENOS Telegram Operating Plan

## Current facts
- Bot: @Newmain97_bot
- Hermes gateway Telegram: active
- Group topics: not available / not enabled for this bot flow
- Bot privacy behavior: command-first / mention-first
- Best reliable pattern: DM for CEO control, group for shared ops commands + important updates only

## Operating model

### Lane 1 — CEO DM
Purpose:
- private control channel
- approvals
- long reports
- build progress

Traffic:
- daily CEO summary
- blocker alerts
- MD-OS build progress
- destructive action approvals if ever needed

### Lane 2 — OPENOS group
Purpose:
- shared operations room
- short commands
- important updates only
- handoff room for future team members

Traffic:
- /status
- /report
- /tasks
- /build
- important alerts only
- no spam metrics

### Lane 3 — local/background
Purpose:
- noisy jobs stay away from Telegram
- logs / drafts / intermediate work stay local

Traffic:
- builder internals
- long traces
- raw health data

## Delivery policy
- Default heavy reports -> DM only
- Group -> only high-signal updates
- No hourly spam
- No duplicated report to DM and group unless critical

## Recommended commands in group
- /help
- /status
- /report
- /tasks
- /build
- /goal
- /agents

## Cron design
1. MD-OS builder every 30m -> DM summary only when real change
2. Morning CEO report -> DM
3. Evening CEO report -> DM
4. Critical failure alert -> group + DM
5. Weekly strategic summary -> DM

## Group setup checklist
1. Bot added as admin
2. Privacy mode understood: commands / mentions are primary trigger
3. Pin one onboarding message with command list
4. First command from group required so Hermes discovers target cleanly
5. After target discovery, create clean group-specific cron/report jobs

## Immediate next step required from group
Send one command inside OPENOS:
- /status
or
- /sethome

This gives Hermes a live group target it can address explicitly.

## After target is discovered
- bind OPENOS as official ops room target
- send pinned onboarding message
- create silent-safe report schedule
- keep DM as CEO lane
