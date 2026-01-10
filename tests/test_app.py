import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pgsql_mcp_server.app import (
    get_schema_names,
    get_tables,
    get_columns,
    get_indexes,
    get_foreign_keys,
    run_dql_query,
    run_ddl_query,
    run_dml_query,
    run_dcl_query
)
from mcp.server.fastmcp import Context

@pytest.fixture
def mock_context():
    ctx = MagicMock(spec=Context)
    # Mocking the nested structure: ctx.request_context.lifespan_context.engine
    ctx.request_context = MagicMock()
    ctx.request_context.lifespan_context = MagicMock()
    ctx.request_context.lifespan_context.engine = MagicMock()
    return ctx

@pytest.mark.asyncio
async def test_get_schema_names(mock_context):
    engine = mock_context.request_context.lifespan_context.engine
    mock_conn = AsyncMock()
    engine.connect.return_value.__aenter__.return_value = mock_conn
    
    # Mock run_sync for inspect().get_schema_names()
    mock_conn.run_sync = AsyncMock(return_value=["public", "information_schema"])
    
    result = await get_schema_names(mock_context)
    assert "All schemas: public, information_schema" in result
    mock_conn.run_sync.assert_called()

@pytest.mark.asyncio
async def test_get_tables(mock_context):
    engine = mock_context.request_context.lifespan_context.engine
    mock_conn = AsyncMock()
    engine.connect.return_value.__aenter__.return_value = mock_conn
    
    mock_conn.run_sync = AsyncMock(return_value=["users", "orders"])
    
    result = await get_tables(mock_context, schema_name="public")
    assert "users" in result
    assert "orders" in result
    assert "Tables in schema 'public'" in result

@pytest.mark.asyncio
async def test_get_columns(mock_context):
    engine = mock_context.request_context.lifespan_context.engine
    mock_conn = AsyncMock()
    engine.connect.return_value.__aenter__.return_value = mock_conn
    
    mock_columns = [
        {"name": "id", "type": "INTEGER", "nullable": False, "autoincrement": True, "default": None, "comment": None},
        {"name": "name", "type": "VARCHAR", "nullable": True, "autoincrement": False, "default": None, "comment": None}
    ]
    mock_conn.run_sync = AsyncMock(return_value=mock_columns)
    
    result = await get_columns(mock_context, table="users")
    assert "id" in result
    assert "INTEGER" in result
    assert "name" in result
    assert "VARCHAR" in result

@pytest.mark.asyncio
async def test_run_dql_query(mock_context):
    engine = mock_context.request_context.lifespan_context.engine
    
    # run_dql_query uses AsyncSession(engine)
    with patch("pgsql_mcp_server.app.AsyncSession") as mock_session_cls:
        mock_session = mock_session_cls.return_value.__aenter__.return_value
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "name"]
        mock_result.fetchall.return_value = [(1, "Alice"), (2, "Bob")]
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await run_dql_query(mock_context, "SELECT * FROM users")
        assert "id" in result
        assert "Alice" in result
        assert "Bob" in result

@pytest.mark.asyncio
async def test_run_dml_query_success(mock_context):
    engine = mock_context.request_context.lifespan_context.engine
    
    with patch("pgsql_mcp_server.app.AsyncSession") as mock_session_cls:
        mock_session = mock_session_cls.return_value.__aenter__.return_value
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        
        result = await run_dml_query(mock_context, "INSERT INTO users (name) VALUES ('Charlie')")
        assert "DML query executed successfully" in result
        assert "Affected rows: 1" in result
        mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_get_indexes(mock_context):
    engine = mock_context.request_context.lifespan_context.engine
    mock_conn = AsyncMock()
    engine.connect.return_value.__aenter__.return_value = mock_conn
    
    mock_indexes = [
        {"name": "idx_users_name", "column_names": ["name"], "unique": False}
    ]
    mock_conn.run_sync = AsyncMock(return_value=mock_indexes)
    
    result = await get_indexes(mock_context, table="users")
    assert "idx_users_name" in result
    assert "name" in result

@pytest.mark.asyncio
async def test_get_foreign_keys(mock_context):
    engine = mock_context.request_context.lifespan_context.engine
    mock_conn = AsyncMock()
    engine.connect.return_value.__aenter__.return_value = mock_conn
    
    mock_fks = [
        {
            "name": "fk_orders_user",
            "constrained_columns": ["user_id"],
            "referred_schema": "public",
            "referred_table": "users",
            "referred_columns": ["id"]
        }
    ]
    mock_conn.run_sync = AsyncMock(return_value=mock_fks)
    
    result = await get_foreign_keys(mock_context, table="orders")
    assert "fk_orders_user" in result
    assert "user_id" in result
    assert "users" in result

@pytest.mark.asyncio
async def test_run_ddl_query_success(mock_context):
    engine = mock_context.request_context.lifespan_context.engine
    
    with patch("pgsql_mcp_server.app.AsyncSession") as mock_session_cls:
        mock_session = mock_session_cls.return_value.__aenter__.return_value
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        
        result = await run_ddl_query(mock_context, "CREATE TABLE temp (id INT)")
        assert "DDL query executed successfully" in result
        mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_run_dcl_query_success(mock_context):
    engine = mock_context.request_context.lifespan_context.engine
    
    with patch("pgsql_mcp_server.app.AsyncSession") as mock_session_cls:
        mock_session = mock_session_cls.return_value.__aenter__.return_value
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        
        result = await run_dcl_query(mock_context, "GRANT SELECT ON users TO guest")
        assert "DCL query executed successfully" in result
        mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_get_tables_error(mock_context):
    engine = mock_context.request_context.lifespan_context.engine
    engine.connect.side_effect = Exception("Connection failed")
    
    result = await get_tables(mock_context, schema_name="public")
    assert "Error occurred while querying table: Connection failed" in result

@pytest.mark.asyncio
async def test_run_dml_query_error(mock_context):
    engine = mock_context.request_context.lifespan_context.engine
    
    with patch("pgsql_mcp_server.app.AsyncSession") as mock_session_cls:
        mock_session = mock_session_cls.return_value.__aenter__.return_value
        mock_session.execute = AsyncMock(side_effect=Exception("Execution failed"))
        mock_session.rollback = AsyncMock()
        
        result = await run_dml_query(mock_context, "DELETE FROM users")
        assert "Unexpected error occurred while executing DML query: Execution failed" in result
        mock_session.rollback.assert_called_once()

@pytest.mark.asyncio
async def test_run_dql_query_no_results(mock_context):
    engine = mock_context.request_context.lifespan_context.engine
    
    with patch("pgsql_mcp_server.app.AsyncSession") as mock_session_cls:
        mock_session = mock_session_cls.return_value.__aenter__.return_value
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "name"]
        mock_result.fetchall.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await run_dql_query(mock_context, "SELECT * FROM users WHERE 1=0")
        assert "Query returned no results." in result
