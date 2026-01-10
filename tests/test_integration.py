import os
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from pgsql_mcp_server.app import (
    app_lifespan,
    get_schema_names,
    get_tables,
    get_columns,
    run_dql_query,
    run_ddl_query,
    run_dml_query
)
from mcp.server.fastmcp import FastMCP, Context

# Integration tests require a local Postgres running on localhost:5432 with database 'postgres'
DSN = os.getenv("DATABASE_URL") or "postgresql+asyncpg://localhost:5432/postgres"

if DSN.startswith("postgresql://"):
    DSN = DSN.replace("postgresql://", "postgresql+asyncpg://", 1)

@pytest_asyncio.fixture()
async def mcp_server():
    server = FastMCP("Test Server")
    from sqlalchemy.ext.asyncio import create_async_engine
    from pgsql_mcp_server.app import AppContext
    
    engine = create_async_engine(DSN, echo=False)
    app_ctx = AppContext(engine=engine)
    try:
        yield server, app_ctx
    finally:
        await engine.dispose()

@pytest_asyncio.fixture
async def mock_context(mcp_server):
    from unittest.mock import MagicMock
    server, app_ctx = mcp_server
    ctx = MagicMock(spec=Context)
    ctx.request_context = MagicMock()
    ctx.request_context.lifespan_context = app_ctx
    return ctx

@pytest.mark.asyncio
async def test_integration_connectivity(mock_context):
    # Verify we can reach the DB and get schemas
    result = await get_schema_names(mock_context)
    assert "public" in result
    assert "All schemas:" in result

@pytest.mark.asyncio
async def test_integration_ddl_dml_dql(mock_context):
    # 1. Create a table (DDL)
    table_name = "test_integration_table"
    await run_ddl_query(mock_context, f"DROP TABLE IF EXISTS {table_name}")
    ddl_result = await run_ddl_query(mock_context, f"CREATE TABLE {table_name} (id SERIAL PRIMARY KEY, name TEXT)")
    assert "DDL query executed successfully" in ddl_result

    # 2. Insert data (DML)
    dml_result = await run_dml_query(mock_context, f"INSERT INTO {table_name} (name) VALUES ('Integration Test')")
    assert "DML query executed successfully" in dml_result
    assert "Affected rows: 1" in dml_result

    # 3. Query data (DQL)
    dql_result = await run_dql_query(mock_context, f"SELECT name FROM {table_name}")
    assert "Integration Test" in dql_result

    # 4. Get table metadata
    tables_result = await get_tables(mock_context, schema_name="public")
    assert table_name in tables_result

    # 5. Get columns
    columns_result = await get_columns(mock_context, table=table_name, schema_name="public")
    assert "id" in columns_result
    assert "name" in columns_result
    assert "text" in columns_result.lower()

    # Cleanup
    await run_ddl_query(mock_context, f"DROP TABLE {table_name}")

@pytest.mark.asyncio
async def test_integration_error_handling(mock_context):
    # Invalid SQL
    with pytest.raises(Exception):
        await run_dql_query(mock_context, "SELECT * FROM non_existent_table")

    ddl_error = await run_ddl_query(mock_context, "CREATE TABLE invalid (id INT PRIMARY KEY, id INT)")
    assert "Error occurred" in ddl_error
