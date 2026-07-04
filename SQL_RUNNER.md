# EXECUTE "healthplus.sql" FROM THE TERMINAL  

```bash
cd healthplus-hospitals-db-project
psql -h localhost -p 5432 -U postgres -d healthplus_db -f sql/healthplus.sql
psql -h localhost -p 5432 -U postgres -d schemas_db -f sql/healthplus.sql
Password for user postgres: give_your_postgres_password
```