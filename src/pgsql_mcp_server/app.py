import os
import click
from sqlmodel import text
from tabulate import tabulate
from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP, Context
from typing import AsyncIterator, Optional
from contextlib import asynccontextmanager
from sqlalchemy.exc import SQLAlchemyError
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
            table_data = [[name] for name in table_names]
            headers = [f"Tables in schema '{schema_name}'"]
            return tabulate(table_data, headers=headers, tablefmt="simple")
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
            headers = [
                "Name",
                "Type",
                "Nullable",
                "Autoincrement",
                "Default",
                "Comment",
            ]
            table_data = [
                [
                    col.get("name"),
                    str(col.get("type")),
                    col.get("nullable"),
                    col.get("autoincrement"),
                    col.get("default"),
                    col.get("comment"),
                ]
                for col in columns
            ]
            table_title = f"Columns for table '{table}'\n\n"
            return table_title + tabulate(
                table_data, headers=headers, tablefmt="simple"
            )

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
            headers = ["Name", "Column Names", "Unique"]
            table_data = [
                [
                    idx.get("name"),
                    ", ".join(idx.get("column_names", [])),
                    idx.get("unique"),
                ]
                for idx in indexes
            ]
            table_title = f"Indexes for table '{table}'\n\n"
            return table_title + tabulate(
                table_data, headers=headers, tablefmt="simple"
            )

    except Exception as e:
        return f"Error occurred while querying table: {str(e)}"


@mcp.tool()
async def get_foreign_keys(
    ctx: Context, table: str, schema_name: Optional[str] = "public"
) -> str:
    """Get foreign keys in a table.

    Args:
        table: The name of the table to get foreign keys from.
        schema_name: The name of the schema to get foreign keys from, defaults to "public".
    """
    try:
        schema_name = schema_name or "public"
        engine = ctx.request_context.lifespan_context.engine

        async with engine.connect() as connection:
            foreign_keys = await connection.run_sync(
                lambda sync_conn: inspect(sync_conn).get_foreign_keys(
                    table, schema=schema_name
                )
            )
        if foreign_keys:
            headers = [
                "Name",
                "Constrained Columns",
                "Referred Schema",
                "Referred Table",
                "Referred Columns",
            ]
            table_data = [
                [
                    fk.get("name"),
                    ", ".join(fk.get("constrained_columns", [])),
                    fk.get("referred_schema"),
                    fk.get("referred_table"),
                    ", ".join(fk.get("referred_columns", [])),
                ]
                for fk in foreign_keys
            ]
            table_title = f"Foreign keys for table '{table}'\n\n"
            return table_title + tabulate(
                table_data, headers=headers, tablefmt="simple"
            )
        else:
            return f"No foreign keys found in table {table}."

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
        keys = result.keys()
        rows = result.fetchall()
        if rows:
            return tabulate(rows, headers=keys, tablefmt="simple")
        else:
            return "Query returned no results."


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
def serve(dsn: str):
    os.environ["DATABASE_URL"] = dsn
    mcp.run()


if __name__ == "__main__":
    serve()
