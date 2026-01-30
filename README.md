# Pulumi Snowflake Template

A production-ready Infrastructure as Code (IaC) template for managing Snowflake resources using Pulumi and Python. This template provides reusable functions for creating and managing users, roles, warehouses, databases, schemas, tables, and access grants in Snowflake.

## Features

- **User Management** - Create users with configurable defaults and security settings
- **Role-Based Access Control** - Define roles and assign them to users
- **Warehouse Management** - Create auto-scaling warehouses with cost controls
- **Database & Schema Organization** - Structure your data with databases and schemas
- **Table Definitions** - Define tables with typed columns and clustering
- **Privilege Grants** - Manage granular access control at all levels
- **Declarative Infrastructure** - All resources defined as code with version control
- **Multi-Environment Support** - Manage dev, staging, and production environments

## Prerequisites

Before using this template, ensure you have:

- [Pulumi CLI](https://www.pulumi.com/docs/get-started/install/) installed
- Python 3.8 or higher
- A Snowflake account with ACCOUNTADMIN or SYSADMIN privileges
- Basic familiarity with Python and Snowflake concepts

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/randalscottking/pulumi-snowflake-template.git
cd pulumi-snowflake-template
```

### 2. Set Up Python Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Initialize Pulumi

```bash
# Use local backend (or omit --local for Pulumi Cloud)
pulumi login --local

# Create a new stack for your environment
pulumi stack init dev
```

### 4. Configure Snowflake Credentials

```bash
# Set your Snowflake account (format: account_locator.region)
pulumi config set snowflake:account xy12345.us-east-1

# Set authentication
pulumi config set snowflake:user ADMIN_USER
pulumi config set --secret snowflake:password YourSecurePassword
pulumi config set snowflake:role ACCOUNTADMIN

# Set environment tag
pulumi config set environment dev
```

### 5. Deploy Infrastructure

```bash
# Preview changes
pulumi preview

# Deploy to Snowflake
pulumi up
```

## Service Account Setup (Recommended for Production)

For automated deployments and CI/CD pipelines, use a service account with key pair authentication instead of personal credentials.

### Option 1: Key Pair Authentication (Most Secure)

**Step 1: Generate Key Pair**

```bash
# Generate private key
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt

# Generate public key from private key
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
```

**Step 2: Create Service Account in Snowflake**

```sql
-- Extract the public key (remove header/footer and concatenate lines)
-- Then create the service account
CREATE USER svc_pulumi_deployer
  COMMENT = 'Service account for Pulumi infrastructure deployment'
  DEFAULT_ROLE = SYSADMIN
  DEFAULT_WAREHOUSE = ADMIN_WH
  RSA_PUBLIC_KEY = 'MIIBIjANBgkqh...';  -- Paste your public key content here

-- Grant necessary role
GRANT ROLE SYSADMIN TO USER svc_pulumi_deployer;

-- Grant additional privileges if needed
GRANT CREATE DATABASE ON ACCOUNT TO ROLE SYSADMIN;
GRANT CREATE WAREHOUSE ON ACCOUNT TO ROLE SYSADMIN;
GRANT CREATE USER ON ACCOUNT TO ROLE SYSADMIN;
```

**Step 3: Configure Pulumi with Key Pair**

```bash
# Set Snowflake account
pulumi config set snowflake:account xy12345.us-east-1

# Set service account user
pulumi config set snowflake:user svc_pulumi_deployer

# Set authentication method to JWT (key pair)
pulumi config set snowflake:authenticator JWT

# Option A: Set private key content directly (recommended for CI/CD)
pulumi config set --secret snowflake:privateKey "$(cat rsa_key.p8)"

# Option B: Set path to private key file (recommended for local development)
pulumi config set snowflake:privateKeyPath /path/to/rsa_key.p8

# Set role
pulumi config set snowflake:role SYSADMIN

# Set environment
pulumi config set environment dev
```

### Option 2: Password Authentication (Less Secure)

For non-production or development environments, you can use password authentication:

```sql
-- Create service account with password
CREATE USER svc_pulumi_deployer
  COMMENT = 'Service account for Pulumi development'
  PASSWORD = 'SecureRandomPassword123!'
  DEFAULT_ROLE = SYSADMIN
  DEFAULT_WAREHOUSE = ADMIN_WH
  MUST_CHANGE_PASSWORD = FALSE;

-- Grant role
GRANT ROLE SYSADMIN TO USER svc_pulumi_deployer;
```

Configure Pulumi:

```bash
pulumi config set snowflake:account xy12345.us-east-1
pulumi config set snowflake:user svc_pulumi_deployer
pulumi config set --secret snowflake:password SecureRandomPassword123!
pulumi config set snowflake:role SYSADMIN
pulumi config set environment dev
```

### Service Account Best Practices

1. **Use Key Pair Authentication** - Always prefer key pairs over passwords for service accounts
2. **Least Privilege** - Use SYSADMIN role instead of ACCOUNTADMIN when possible
3. **Separate Accounts** - Create different service accounts for different purposes:
   - `svc_pulumi_dev` - Development deployments
   - `svc_pulumi_prod` - Production deployments
   - `svc_ci_cd` - CI/CD pipeline deployments
4. **Key Rotation** - Rotate private keys every 90-180 days
5. **Secure Storage** - Store private keys in secure vaults (AWS Secrets Manager, Azure Key Vault, HashiCorp Vault)
6. **Audit Logging** - Regularly review service account activity in Snowflake
7. **No Interactive Login** - Service accounts should never be used for interactive sessions

### CI/CD Integration Example

For GitHub Actions:

```yaml
# .github/workflows/deploy.yml
name: Deploy Snowflake Infrastructure

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Configure Pulumi
        run: |
          pulumi login --local
          pulumi stack select prod
        env:
          PULUMI_CONFIG_PASSPHRASE: ${{ secrets.PULUMI_CONFIG_PASSPHRASE }}
      
      - name: Deploy with Service Account
        run: pulumi up --yes
        env:
          SNOWFLAKE_ACCOUNT: ${{ secrets.SNOWFLAKE_ACCOUNT }}
          SNOWFLAKE_USER: svc_pulumi_deployer
          SNOWFLAKE_PRIVATE_KEY: ${{ secrets.SNOWFLAKE_PRIVATE_KEY }}
          SNOWFLAKE_ROLE: SYSADMIN
          SNOWFLAKE_AUTHENTICATOR: JWT
```

## Project Structure

```
pulumi-snowflake-template/
├── main.py              # Main Pulumi program with helper functions
├── Pulumi.yaml          # Pulumi project configuration
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Usage Guide

### Helper Functions

The template provides the following reusable functions in `main.py`:

#### User Management
- `create_user()` - Create a Snowflake user with defaults
- `create_role()` - Define a new role
- `grant_role_to_user()` - Assign a role to a user

#### Infrastructure
- `create_warehouse()` - Create a virtual warehouse
- `create_database()` - Create a database
- `create_schema()` - Create a schema within a database
- `create_table()` - Create a table with typed columns

#### Access Control
- `grant_database_usage()` - Grant USAGE on database
- `grant_schema_usage()` - Grant USAGE on schema
- `grant_table_select()` - Grant SELECT on tables
- `grant_warehouse_usage()` - Grant USAGE on warehouse

### Example: Creating a Complete Environment

Here's how to create a user, database, and table with proper permissions:

```python
import pulumi
import pulumi_snowflake as snowflake

# 1. Create a warehouse
analytics_wh = create_warehouse(
    "analytics-warehouse",
    warehouse_size="MEDIUM",
    auto_suspend=600,  # 10 minutes
)

# 2. Create a role
analyst_role = create_role(
    "analyst-role",
    comment="Role for data analysts",
)

# 3. Create a user
analyst_user = create_user(
    name="analyst-user",
    login_name="JOHN_DOE",
    email="john.doe@company.com",
    default_role=analyst_role.name,
    default_warehouse=analytics_wh.name,
)

# 4. Grant role to user
grant_role_to_user(
    "analyst-role-grant",
    role_name=analyst_role.name,
    user_name=analyst_user.name,
)

# 5. Create database and schema
sales_db = create_database(
    "sales-database",
    comment="Sales and revenue data",
    data_retention_time_in_days=7,
)

transactions_schema = create_schema(
    "transactions-schema",
    database=sales_db.name,
    schema_name="TRANSACTIONS",
    comment="Transaction records",
)

# 6. Create a table
orders_table = create_table(
    name="orders-table",
    database=sales_db.name,
    schema=transactions_schema.name,
    table_name="ORDERS",
    columns=[
        {"name": "ORDER_ID", "type": "NUMBER(38,0)", "nullable": "false"},
        {"name": "CUSTOMER_ID", "type": "NUMBER(38,0)", "nullable": "false"},
        {"name": "ORDER_DATE", "type": "TIMESTAMP_NTZ", "nullable": "false"},
        {"name": "TOTAL_AMOUNT", "type": "NUMBER(38,2)", "nullable": "false"},
        {"name": "STATUS", "type": "VARCHAR(50)", "nullable": "false"},
    ],
    comment="Order transactions",
    cluster_by=["ORDER_DATE", "CUSTOMER_ID"],
)

# 7. Grant permissions to the role
grant_database_usage("db-grant", sales_db.name, analyst_role.name)
grant_schema_usage("schema-grant", sales_db.name, transactions_schema.name, analyst_role.name)
grant_table_select("table-grant", sales_db.name, transactions_schema.name, analyst_role.name)
grant_warehouse_usage("wh-grant", analytics_wh.name, analyst_role.name)

# 8. Export important values
pulumi.export("warehouse", analytics_wh.name)
pulumi.export("database", sales_db.name)
pulumi.export("user", analyst_user.name)
```

### Example: Table with Different Column Types

```python
feature_table = create_table(
    name="customer-features",
    database=analytics_db.name,
    schema=analytics_schema.name,
    table_name="CUSTOMER_FEATURES",
    columns=[
        # Numeric types
        {"name": "CUSTOMER_ID", "type": "NUMBER(38,0)", "nullable": "false"},
        {"name": "LIFETIME_VALUE", "type": "NUMBER(38,2)", "nullable": "true"},
        {"name": "SCORE", "type": "FLOAT", "nullable": "true"},
        
        # String types
        {"name": "SEGMENT", "type": "VARCHAR(100)", "nullable": "true"},
        {"name": "NOTES", "type": "TEXT", "nullable": "true"},
        
        # Date/Time types
        {"name": "FIRST_PURCHASE", "type": "DATE", "nullable": "true"},
        {"name": "LAST_UPDATED", "type": "TIMESTAMP_NTZ", "nullable": "false"},
        
        # Boolean type
        {"name": "IS_ACTIVE", "type": "BOOLEAN", "nullable": "false"},
        
        # Semi-structured type
        {"name": "METADATA", "type": "VARIANT", "nullable": "true"},
    ],
    comment="Customer analytics features",
    cluster_by=["CUSTOMER_ID"],
)
```

## Common Snowflake Data Types

| Category | Types | Example |
|----------|-------|---------|
| **Numeric** | `NUMBER(p,s)`, `INTEGER`, `FLOAT`, `DOUBLE` | `NUMBER(38,2)` |
| **String** | `VARCHAR(n)`, `STRING`, `TEXT`, `CHAR(n)` | `VARCHAR(255)` |
| **Date/Time** | `DATE`, `TIMESTAMP_NTZ`, `TIMESTAMP_LTZ`, `TIME` | `TIMESTAMP_NTZ` |
| **Boolean** | `BOOLEAN` | `BOOLEAN` |
| **Semi-structured** | `VARIANT`, `OBJECT`, `ARRAY` | `VARIANT` |
| **Binary** | `BINARY`, `VARBINARY` | `BINARY` |

## Managing Multiple Environments

Use Pulumi stacks to manage separate environments:

```bash
# Create stacks for each environment
pulumi stack init dev
pulumi stack init staging
pulumi stack init prod

# Switch between environments
pulumi stack select dev

# Each stack has its own configuration
pulumi config set snowflake:account dev-account.us-east-1
pulumi config set environment dev
```

## Best Practices

1. **Security**
   - Always use `--secret` flag for passwords and sensitive data
   - Follow principle of least privilege when granting permissions
   - Enable MFA on administrative Snowflake accounts

2. **Cost Management**
   - Set appropriate `auto_suspend` times on warehouses (300-600 seconds)
   - Start with smaller warehouse sizes and scale up as needed
   - Use `initially_suspended=True` to avoid immediate costs

3. **Resource Organization**
   - Use consistent naming conventions (e.g., `<env>-<purpose>-<type>`)
   - Add meaningful comments to all resources
   - Configure appropriate data retention periods

4. **Version Control**
   - Commit your `main.py` changes to git
   - Never commit `Pulumi.*.yaml` files (contains config/secrets)
   - Use `.gitignore` to protect sensitive files

5. **Testing**
   - Always run `pulumi preview` before `pulumi up`
   - Test infrastructure changes in dev environment first
   - Use separate Snowflake accounts for dev/staging/prod

## Configuration Reference

### Required Configuration (Password Authentication)

```bash
snowflake:account      # Snowflake account identifier
snowflake:user         # User for authentication
snowflake:password     # User password (use --secret)
snowflake:role         # Role to assume (ACCOUNTADMIN or SYSADMIN)
```

### Required Configuration (Key Pair Authentication - Recommended)

```bash
snowflake:account        # Snowflake account identifier
snowflake:user           # Service account user
snowflake:authenticator  # Set to "JWT" for key pair auth
snowflake:privateKey     # Private key content (use --secret), OR
snowflake:privateKeyPath # Path to private key file
snowflake:role          # Role to assume (typically SYSADMIN)
```

### Optional Configuration

```bash
environment            # Environment name (dev/staging/prod)
snowflake:region       # Snowflake region (default: us-east-1)
```

## Warehouse Sizing Guide

| Size | Credits/Hour | Use Case |
|------|-------------|----------|
| X-SMALL | 1 | Light queries, development |
| SMALL | 2 | Small datasets, testing |
| MEDIUM | 4 | Standard workloads |
| LARGE | 8 | Heavy analytics |
| X-LARGE | 16 | Data engineering |
| 2X-LARGE | 32 | Large-scale processing |

## Common Commands

```bash
# View current configuration
pulumi config

# Preview changes
pulumi preview

# Deploy infrastructure
pulumi up

# View outputs
pulumi stack output

# Destroy all resources
pulumi destroy

# View stack history
pulumi stack history

# Export stack configuration
pulumi stack export > stack-backup.json
```

## Troubleshooting

### Authentication Errors

If you encounter authentication issues:

1. Verify your Snowflake account identifier format
2. Test credentials with SnowSQL: `snowsql -a <account> -u <user>`
3. Ensure your user has sufficient privileges
4. Check if your Snowflake account is active

### Resource Already Exists

If a resource already exists in Snowflake:

```bash
# Import existing resource
pulumi import snowflake:index/database:Database my-db MY_DATABASE_NAME
```

### Permission Denied

Ensure your Snowflake user has the required privileges:

```sql
-- Grant necessary privileges (run in Snowflake)
GRANT CREATE DATABASE ON ACCOUNT TO ROLE SYSADMIN;
GRANT CREATE USER ON ACCOUNT TO ROLE ACCOUNTADMIN;
GRANT CREATE WAREHOUSE ON ACCOUNT TO ROLE SYSADMIN;
```

## Updating the Template

To update resources:

1. Modify `main.py` with your changes
2. Run `pulumi preview` to see the diff
3. Run `pulumi up` to apply changes
4. Pulumi automatically handles updates vs. replacements

## Destroying Resources

To tear down infrastructure:

```bash
# Preview what will be destroyed
pulumi destroy --preview

# Destroy all resources
pulumi destroy
```

**Warning**: This will permanently delete all resources managed by this stack. Use with caution in production environments.

## Resources

- [Pulumi Documentation](https://www.pulumi.com/docs/)
- [Pulumi Snowflake Provider](https://www.pulumi.com/registry/packages/snowflake/)
- [Snowflake Documentation](https://docs.snowflake.com/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

## Author

**Randal Scott King**
- GitHub: [@randalscottking](https://github.com/randalscottking)
- Website: [randalscottking.com](https://randalscottking.com)

## Acknowledgments

- Built with [Pulumi](https://www.pulumi.com/)
- Powered by [Snowflake](https://www.snowflake.com/)

---

**Need help?** [Open an issue](https://github.com/randalscottking/pulumi-snowflake-template/issues) or reach out via GitHub.
