# 🛠️ Troubleshooting: Database Does Not Exist

If you encounter the error `250001 (08001): None: DB 'HYPERLOGISTICS_DB' does not exist`, follow these steps:

### 1. Execute Creation Script
Ensure you have run the foundation script:
`src/sql/00_create_database.sql`

### 2. Check Context
Manually set your worksheet context in Snowflake:
```sql
USE DATABASE HYPERLOGISTICS_DB;
USE ROLE ACCOUNTADMIN;
```

### 3. Case Sensitivity
Snowflake identifiers are case-insensitive unless double-quoted. Ensure your `.env` file matches the case from `SHOW DATABASES;`:
`SNOWFLAKE_DATABASE=HYPERLOGISTICS_DB`

### 4. Role Permissions
The database might exist but be invisible to your current role. Grant usage to your user role:
```sql
GRANT USAGE ON DATABASE HYPERLOGISTICS_DB TO ROLE your_role;
```
