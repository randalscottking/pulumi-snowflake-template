"""
Snowflake Infrastructure as Code with Pulumi
Manages users, roles, databases, schemas, and tables
"""

import pulumi
import pulumi_snowflake as snowflake
from typing import List, Dict, Optional

# Configuration
config = pulumi.Config()
environment = config.get("environment") or "dev"

# ============================================================================
# USERS
# ============================================================================

def create_user(
    name: str,
    login_name: str,
    email: str,
    default_role: Optional[str] = None,
    default_warehouse: Optional[str] = None,
    default_namespace: Optional[str] = None,
    must_change_password: bool = True,
    disabled: bool = False,
) -> snowflake.User:
    """
    Create a Snowflake user with standard configuration.
    
    Args:
        name: Pulumi resource name
        login_name: Snowflake login name
        email: User email address
        default_role: Default role for the user
        default_warehouse: Default warehouse
        default_namespace: Default database.schema
        must_change_password: Force password change on first login
        disabled: Whether the user is disabled
    """
    return snowflake.User(
        name,
        name=login_name,
        login_name=login_name,
        email=email,
        default_role=default_role,
        default_warehouse=default_warehouse,
        default_namespace=default_namespace,
        must_change_password=must_change_password,
        disabled=disabled,
        comment=f"Managed by Pulumi - {environment}",
    )


# ============================================================================
# ROLES
# ============================================================================

def create_role(name: str, comment: Optional[str] = None) -> snowflake.Role:
    """Create a Snowflake role."""
    return snowflake.Role(
        name,
        name=name,
        comment=comment or f"Managed by Pulumi - {environment}",
    )


# ============================================================================
# ROLE GRANTS (User to Role assignments)
# ============================================================================

def grant_role_to_user(
    name: str,
    role_name: pulumi.Input[str],
    user_name: pulumi.Input[str],
) -> snowflake.RoleGrants:
    """Grant a role to a user."""
    return snowflake.RoleGrants(
        name,
        role_name=role_name,
        users=[user_name],
    )


# ============================================================================
# WAREHOUSES
# ============================================================================

def create_warehouse(
    name: str,
    warehouse_size: str = "SMALL",
    auto_suspend: int = 300,
    auto_resume: bool = True,
    initially_suspended: bool = True,
    max_cluster_count: int = 1,
    min_cluster_count: int = 1,
) -> snowflake.Warehouse:
    """
    Create a Snowflake warehouse with auto-scaling configuration.
    
    Args:
        name: Warehouse name
        warehouse_size: Size (X-SMALL, SMALL, MEDIUM, LARGE, X-LARGE, etc.)
        auto_suspend: Seconds of inactivity before auto-suspend
        auto_resume: Auto-resume on query
        initially_suspended: Start in suspended state
        max_cluster_count: Maximum clusters for auto-scaling
        min_cluster_count: Minimum clusters
    """
    return snowflake.Warehouse(
        name,
        name=name,
        warehouse_size=warehouse_size,
        auto_suspend=auto_suspend,
        auto_resume=auto_resume,
        initially_suspended=initially_suspended,
        max_cluster_count=max_cluster_count,
        min_cluster_count=min_cluster_count,
        comment=f"Managed by Pulumi - {environment}",
    )


# ============================================================================
# DATABASES
# ============================================================================

def create_database(
    name: str,
    comment: Optional[str] = None,
    data_retention_time_in_days: int = 1,
) -> snowflake.Database:
    """
    Create a Snowflake database.
    
    Args:
        name: Database name
        comment: Optional comment
        data_retention_time_in_days: Time travel retention period
    """
    return snowflake.Database(
        name,
        name=name,
        comment=comment or f"Managed by Pulumi - {environment}",
        data_retention_time_in_days=data_retention_time_in_days,
    )


# ============================================================================
# SCHEMAS
# ============================================================================

def create_schema(
    name: str,
    database: pulumi.Input[str],
    schema_name: str,
    comment: Optional[str] = None,
    data_retention_days: Optional[int] = None,
    is_managed: bool = False,
) -> snowflake.Schema:
    """
    Create a Snowflake schema.
    
    Args:
        name: Pulumi resource name
        database: Database name
        schema_name: Schema name
        comment: Optional comment
        data_retention_days: Override database retention setting
        is_managed: Whether this is a managed schema
    """
    return snowflake.Schema(
        name,
        database=database,
        name=schema_name,
        comment=comment or f"Managed by Pulumi - {environment}",
        data_retention_days=data_retention_days,
        is_managed=is_managed,
    )


# ============================================================================
# TABLES
# ============================================================================

def create_table(
    name: str,
    database: pulumi.Input[str],
    schema: pulumi.Input[str],
    table_name: str,
    columns: List[Dict[str, str]],
    comment: Optional[str] = None,
    cluster_by: Optional[List[str]] = None,
) -> snowflake.Table:
    """
    Create a Snowflake table.
    
    Args:
        name: Pulumi resource name
        database: Database name
        schema: Schema name
        table_name: Table name
        columns: List of column definitions with 'name', 'type', and optional 'nullable'
        comment: Optional comment
        cluster_by: Optional clustering keys
    
    Example columns:
        [
            {"name": "ID", "type": "NUMBER(38,0)", "nullable": "false"},
            {"name": "NAME", "type": "VARCHAR(100)", "nullable": "true"},
            {"name": "CREATED_AT", "type": "TIMESTAMP_NTZ", "nullable": "false"},
        ]
    """
    column_specs = [
        snowflake.TableColumnArgs(
            name=col["name"],
            type=col["type"],
            nullable=col.get("nullable", "true") == "true",
        )
        for col in columns
    ]
    
    return snowflake.Table(
        name,
        database=database,
        schema=schema,
        name=table_name,
        columns=column_specs,
        comment=comment or f"Managed by Pulumi - {environment}",
        cluster_bys=cluster_by,
    )


# ============================================================================
# GRANTS
# ============================================================================

def grant_database_usage(
    name: str,
    database_name: pulumi.Input[str],
    role: pulumi.Input[str],
) -> snowflake.GrantPrivilegesToAccountRole:
    """Grant USAGE privilege on database to a role."""
    return snowflake.GrantPrivilegesToAccountRole(
        name,
        account_role_name=role,
        privileges=["USAGE"],
        on_account_object=snowflake.GrantPrivilegesToAccountRoleOnAccountObjectArgs(
            object_type="DATABASE",
            object_name=database_name,
        ),
    )


def grant_schema_usage(
    name: str,
    database_name: pulumi.Input[str],
    schema_name: pulumi.Input[str],
    role: pulumi.Input[str],
) -> snowflake.GrantPrivilegesToAccountRole:
    """Grant USAGE privilege on schema to a role."""
    return snowflake.GrantPrivilegesToAccountRole(
        name,
        account_role_name=role,
        privileges=["USAGE"],
        on_schema=snowflake.GrantPrivilegesToAccountRoleOnSchemaArgs(
            schema_name=pulumi.Output.concat(database_name, ".", schema_name),
        ),
    )


def grant_table_select(
    name: str,
    database_name: pulumi.Input[str],
    schema_name: pulumi.Input[str],
    role: pulumi.Input[str],
    all_tables: bool = True,
) -> snowflake.GrantPrivilegesToAccountRole:
    """Grant SELECT privilege on tables to a role."""
    if all_tables:
        return snowflake.GrantPrivilegesToAccountRole(
            name,
            account_role_name=role,
            privileges=["SELECT"],
            on_schema_object=snowflake.GrantPrivilegesToAccountRoleOnSchemaObjectArgs(
                all=snowflake.GrantPrivilegesToAccountRoleOnSchemaObjectAllArgs(
                    object_type_plural="TABLES",
                    in_schema=pulumi.Output.concat(database_name, ".", schema_name),
                ),
            ),
        )


def grant_warehouse_usage(
    name: str,
    warehouse_name: pulumi.Input[str],
    role: pulumi.Input[str],
) -> snowflake.GrantPrivilegesToAccountRole:
    """Grant USAGE privilege on warehouse to a role."""
    return snowflake.GrantPrivilegesToAccountRole(
        name,
        account_role_name=role,
        privileges=["USAGE"],
        on_account_object=snowflake.GrantPrivilegesToAccountRoleOnAccountObjectArgs(
            object_type="WAREHOUSE",
            object_name=warehouse_name,
        ),
    )

# ============================================================================
# EXPORTS
# ============================================================================

pulumi.export("warehouse", example_wh.name)
pulumi.export("database", example_db.name)
pulumi.export("schema", example_schema.name)
pulumi.export("table", example_table.name)
pulumi.export("user", example_user.name)
pulumi.export("role", example_role.name)
