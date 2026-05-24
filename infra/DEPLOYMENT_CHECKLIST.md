# MD-OS Deployment Checklist

## Preflight
- Backup DB
- Verify `.env` secrets present, not committed
- Run migrations dry-run
- Run test suite
- Verify Hermes Gateway health
- Verify Paperclip health
- Verify 9Router model route health

## Deploy
1. Build backend
2. Build Paperclip UI
3. Apply migrations
4. Seed default data
5. Start services
6. Run smoke tests
7. Enable cron/timers only after approval

## Smoke Tests
- `/api/health`
- `/api/companies`
- `/api/agents`
- `/api/workflows`
- Paperclip page loads no console errors
- Login works
- Agent run creates task and audit log

## Rollback
- Stop new workers
- Restore previous service image
- Restore DB backup if migration failed
- Re-run smoke tests
