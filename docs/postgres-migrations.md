# PostgreSQL + pgvector migrations

## Dev database

```bash
docker compose -f infra/docker-compose.postgres.yml up -d
export POSTGRES_URI="postgresql://md_os:md_os_dev_password@localhost:5432/md_os"
python -c "from api.db import init_db; print(init_db())"
```

## Migration behavior

- Files from `/root/md-os/schemas/*.sql` run in sorted order.
- `_migrations.version` stores full filename stem, e.g. `001_initial`, `001_core_schema`, `002_seed_data`.
- Full stem avoids collision when multiple migration files share numeric prefix.
- Without `POSTGRES_URI`, API uses in-memory store for tests/dev.
