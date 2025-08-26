# Database Migration Helper

This script helps migrate data from an in-memory SQLite database to the new file-backed database.

## Usage

1. **Stop the application** if it's running
2. **Run the migration script** (see below)
3. **Restart the application** with the new database

## Migration Script

```python
#!/usr/bin/env python3
"""One-time migration script to move from in-memory to file-backed SQLite."""

import os
from pathlib import Path
from sqlmodel import Session, SQLModel, create_engine

# Import models
from app.models import Tenant, AgentSettings, ExternalAgent, Product

def migrate_to_file_db():
    """Migrate data from current database to file-backed database."""
    
    # Ensure data directory exists
    Path("./data").mkdir(exist_ok=True)
    
    # Source database (current)
    source_url = "sqlite:///./adcp_demo.db"  # Adjust if different
    source_engine = create_engine(source_url)
    
    # Target database (new file-backed)
    target_url = "sqlite:///./data/adcp_demo.sqlite3"
    target_engine = create_engine(target_url)
    
    # Create tables in target
    SQLModel.metadata.create_all(target_engine)
    
    # Migrate data
    with Session(source_engine) as source_session, Session(target_engine) as target_session:
        # Migrate tenants
        tenants = source_session.exec("SELECT * FROM tenant").fetchall()
        for tenant_data in tenants:
            tenant = Tenant(**dict(tenant_data))
            target_session.add(tenant)
        
        # Migrate agent settings
        agent_settings = source_session.exec("SELECT * FROM agentsettings").fetchall()
        for setting_data in agent_settings:
            setting = AgentSettings(**dict(setting_data))
            target_session.add(setting)
        
        # Migrate external agents
        external_agents = source_session.exec("SELECT * FROM externalagent").fetchall()
        for agent_data in external_agents:
            agent = ExternalAgent(**dict(agent_data))
            target_session.add(agent)
        
        # Migrate products
        products = source_session.exec("SELECT * FROM product").fetchall()
        for product_data in products:
            product = Product(**dict(product_data))
            target_session.add(product)
        
        target_session.commit()
    
    print(f"Migration completed. Data moved to {target_url}")

if __name__ == "__main__":
    migrate_to_file_db()
```

## Manual Migration Steps

If you prefer manual migration:

1. **Copy existing database file** (if using file-based SQLite):
   ```bash
   cp adcp_demo.db ./data/adcp_demo.sqlite3
   ```

2. **Recreate data** (if using in-memory SQLite):
   - Start the application
   - Create tenants via the UI at `/tenants`
   - The data will now persist in the new file location

## Verification

After migration, verify data persistence:

1. **Check database file exists**:
   ```bash
   ls -la ./data/adcp_demo.sqlite3
   ```

2. **Restart the application** and verify data is still present

3. **Run persistence tests**:
   ```bash
   pytest tests/test_db_persistence.py -v
   ```

## Cleanup

After successful migration:

1. **Delete the migration script**: `rm scripts/migrate_to_file_db.md`
2. **Remove old database file** (if exists): `rm adcp_demo.db`
3. **Update .env**: Ensure `DATABASE_URL=sqlite:///./data/adcp_demo.sqlite3`
