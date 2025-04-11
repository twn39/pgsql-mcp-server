import os
import click
from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP, Context
from typing import AsyncIterator, Optional
from contextlib import asynccontextmanager
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import text
from sqlalchemy import inspect, Result
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession


@dataclass
class AppContext:
    engine: AsyncEngine


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    _dsn = os.getenv("DATABASE_URL")
    if not _dsn:
        raise ValueError("DATABASE_URL environment variable not set.")
    if _dsn.startswith("postgresql://"):
        _dsn = _dsn.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(_dsn, echo=False)

    try:
        yield AppContext(engine=engine)
    finally:
        await engine.dispose()


mcp = FastMCP("PgSQL MCP Server", lifespan=app_lifespan)


@mcp.tool()
async def get_schema_names(ctx: Context) -> str:
    """Get all schema names."""
    engine = ctx.request_context.lifespan_context.engine

    async with engine.connect() as connection:
        schema_names = await connection.run_sync(
            lambda sync_conn: inspect(sync_conn).get_schema_names()
        )
    if not schema_names:
        return "No schemas found."
    else:
        return f"All schemas: {', '.join(schema_names)}"


@mcp.tool()
async def get_tables(ctx: Context, schema_name: Optional[str] = "public") -> str:
    """Get all tables in a schema.

    Args:
        schema_name: The name of the schema to get tables from, defaults to "public".
    """
    try:
        schema_name = schema_name or "public"
        engine = ctx.request_context.lifespan_context.engine

        async with engine.connect() as connection:
            table_names = await connection.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names(schema=schema_name)
            )
        if table_names:
            return f"All tables from schema {schema_name}: {', '.join(table_names)}"
        else:
            return f"No tables found in schema {schema_name}."

    except Exception as e:
        return f"Error occurred while querying table: {str(e)}"


@mcp.tool()
async def get_columns(
    ctx: Context, table: str, schema_name: Optional[str] = "public"
) -> str:
    """Get all columns in a table.

    Args:
        table: The name of the table to get columns from.
        schema_name: The name of the schema to get columns from, defaults to "public".
    """
    try:
        schema_name = schema_name or "public"
        engine = ctx.request_context.lifespan_context.engine
        async with engine.connect() as connection:
            columns = await connection.run_sync(
                lambda sync_conn: inspect(sync_conn).get_columns(
                    table, schema=schema_name
                )
            )

        if not columns:
            return "No columns found in table."
        else:
            return str(columns)

    except Exception as e:
        return f"Error occurred while querying table: {str(e)}"


@mcp.tool()
async def get_indexes(
    ctx: Context, table: str, schema_name: Optional[str] = "public"
) -> str:
    """Get all indexes in a table.

    Args:
        table: The name of the table to get indexes from.
        schema_name: The name of the schema to get indexes from, defaults to "public".
    """
    try:
        schema_name = schema_name or "public"
        engine = ctx.request_context.lifespan_context.engine

        async with engine.connect() as connection:
            indexes = await connection.run_sync(
                lambda sync_conn: inspect(sync_conn).get_indexes(
                    table, schema=schema_name
                )
            )

        if not indexes:
            return "No indexes found in table."
        else:
            return str(indexes)

    except Exception as e:
        return f"Error occurred while querying table: {str(e)}"


@mcp.tool()
async def run_dql_query(ctx: Context, raw_dql_sql: str) -> str:
    """Run a raw DQL SQL query, like SELECT, SHOW, DESCRIBE, EXPLAIN, etc.

    Args:
        raw_dql_sql: The raw DQL SQL query to run.
    """
    engine = ctx.request_context.lifespan_context.engine
    async with AsyncSession(engine) as session:
        raw_sql_select = text(raw_dql_sql)
        result: Result = await session.execute(raw_sql_select)
        rows = result.fetchall()
        return str(rows)


@mcp.tool()
async def run_ddl_query(ctx: Context, raw_ddl_sql: str) -> str:
    """Run a raw DDL SQL query, like CREATE, ALTER, DROP, etc.
    Args:
        raw_ddl_sql: The raw DDL SQL query to run.
    """
    engine = ctx.request_context.lifespan_context.engine
    async with AsyncSession(engine) as session:
        try:
            await session.execute(text(raw_ddl_sql))
            await session.commit()
            return "DDL query executed successfully."
        except SQLAlchemyError as e:
            await session.rollback()
            return f"Error occurred while executing DDL query: {str(e)}"
        except Exception as e:
            await session.rollback()
            return f"Unexpected error occurred while executing DDL query: {str(e)}"


@mcp.tool()
async def run_dml_query(ctx: Context, raw_dml_sql: str) -> str:
    """Run a raw DDL query, like INSERT, UPDATE, DELETE, etc.
    Args:
        raw_dml_sql: The raw DDL SQL query to run.
    """
    engine = ctx.request_context.lifespan_context.engine
    async with AsyncSession(engine) as session:
        try:
            result = await session.execute(text(raw_dml_sql))
            await session.commit()  # Commit transaction to save changes
            return f"DML query executed successfully. Affected rows: {result.rowcount}"
        except SQLAlchemyError as e:
            await session.rollback()
            return f"Error occurred while executing DML query: {str(e)}"
        except Exception as e:
            await session.rollback()
            return f"Unexpected error occurred while executing DML query: {str(e)}"


@mcp.tool()
async def run_dcl_query(ctx: Context, raw_dcl_sql: str) -> str:
    """Run a raw DCL SQL query, like GRANT, REVOKE, etc.
    Args:
        raw_dcl_sql: The raw DDL SQL query to run.
    """
    engine = ctx.request_context.lifespan_context.engine
    async with AsyncSession(engine) as session:
        try:
            await session.execute(text(raw_dcl_sql))
            await session.commit()
            return "DCL query executed successfully."
        except SQLAlchemyError as e:
            await session.rollback()
            return f"Error occurred while executing DCL query: {str(e)}"
        except Exception as e:
            await session.rollback()
            return f"Unexpected error occurred while executing DCL query: {str(e)}"


@click.command()
@click.option("--dsn", "-d", type=str, help="Database connection string")
@click.option("-v", "--verbose", count=True)
def serve(dsn: str, verbose: bool):
    os.environ["DATABASE_URL"] = dsn
    mcp.run()


if __name__ == "__main__":
    serve()
