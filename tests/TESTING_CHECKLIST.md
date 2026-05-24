# MD-OS Testing Checklist

## Unit
- Agent definition schema validates
- Workflow graph schema validates
- Approval guard catches destructive/financial/production/customer-data/secret actions
- RBAC blocks cross-company access
- Memory search respects company_id

## Integration
- Create company → project → agents → team → task
- Run workflow with condition branch
- Agent requests approval and pauses
- Approval resumes run
- Audit log records all mutations
- Connector health check works

## E2E
- User opens Paperclip dashboard
- Creates agent in Agent Studio
- Builds workflow in Workflow Studio
- Runs task from Project Workspace
- Receives approval request
- Approves and sees completion report

## Security
- No secrets in logs
- No cross-tenant data leak
- All mutations audited
- Production deploy requires approval
- Customer data export requires approval

## Performance
- Dashboard < 2s p95
- Workflow run status < 500ms p95
- Memory search < 1s p95 for 100k memories
- Agent queue handles 100 concurrent tasks
