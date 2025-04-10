import os
import click
from textwrap import dedent
from dataclasses import dataclass
from sqlalchemy.engine import Engine
from mcp.server.fastmcp import FastMCP, Context
from typing import AsyncIterator, Optional
from contextlib import asynccontextmanager
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import create_engine, Session, text
from sqlalchemy import inspect, Result


@dataclass
class AppContext:
    engine: Engine


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    _dsn = os.getenv("DATABASE_URL")
    engine = create_engine(_dsn, echo=False)

    try:
        yield AppContext(engine=engine)
    finally:
        engine.dispose()


mcp = FastMCP("PostgreSQL Explorer", lifespan=app_lifespan)


@mcp.tool()
def get_schema_names(ctx: Context) -> str:
    """Get all schema names."""
    engine = ctx.request_context.lifespan_context.engine
    inspector = inspect(engine)

    schema_names = inspector.get_schema_names()
    if not inspector.get_schema_names():
        return "No schemas found."
    else:
        return f"All schemas: {', '.join(schema_names)}"


@mcp.tool()
def get_tables(ctx: Context, schema_name: Optional[str] = "public") -> str:
    """Get all tables in a schema.

    Args:
        schema_name: The name of the schema to get tables from, defaults to "public".
    """
    try:
        schema_name = schema_name or "public"
        engine = ctx.request_context.lifespan_context.engine
        inspector = inspect(engine)

        table_names = inspector.get_table_names(schema=schema_name)
        if table_names:
            return f"All tables from schema {schema_name}: {', '.join(table_names)}"
        else:
            return f"No tables found in schema {schema_name}."

    except Exception as e:
        return f"查询表时发生错误: {str(e)}"


@mcp.tool()
def get_columns(ctx: Context, table: str, schema_name: Optional[str] = "public") -> str:
    """Get all columns in a table.

    Args:
        table: The name of the table to get columns from.
        schema_name: The name of the schema to get columns from, defaults to "public".
    """
    try:
        schema_name = schema_name or "public"
        engine = ctx.request_context.lifespan_context.engine
        inspector = inspect(engine)
        columns = inspector.get_columns(table, schema=schema_name)

        if not columns:
            return "No columns found in table."
        else:
            return str(columns)

    except Exception as e:
        return f"查询表时发生错误: {str(e)}"


@mcp.tool()
def get_indexes(ctx: Context, table: str, schema_name: Optional[str] = "public") -> str:
    """Get all indexes in a table.

    Args:
        table: The name of the table to get indexes from.
        schema_name: The name of the schema to get indexes from, defaults to "public".
    """
    try:
        schema_name = schema_name or "public"
        engine = ctx.request_context.lifespan_context.engine
        inspector = inspect(engine)
        indexes = inspector.get_indexes(table, schema=schema_name)

        if not indexes:
            return "No indexes found in table."
        else:
            return str(indexes)

    except Exception as e:
        return f"查询表时发生错误: {str(e)}"


@mcp.tool()
def run_dql_query(ctx: Context, raw_dql_sql: str) -> str:
    """Run a raw DQL SQL query, like SELECT, SHOW, DESCRIBE, EXPLAIN, etc.

    Args:
        raw_dql_sql: The raw DQL SQL query to run.
    """
    engine = ctx.request_context.lifespan_context.engine
    with Session(engine) as session:
        raw_sql_select = text(raw_dql_sql)
        result: Result = session.execute(raw_sql_select)
        rows = result.fetchall()
        return str(rows)


@mcp.tool()
def run_ddl_query(ctx: Context, raw_ddl_sql: str) -> str:
    """Run a raw DDL SQL query, like CREATE, ALTER, DROP, etc.
    Args:
        raw_ddl_sql: The raw DDL SQL query to run.
    """
    engine = ctx.request_context.lifespan_context.engine
    with Session(engine) as session:
        try:
            session.execute(text(raw_ddl_sql))
            session.commit()  # 提交事务以使 DDL 生效
            return "DDL 查询成功执行。"
        except SQLAlchemyError as e:
            session.rollback()  # 回滚事务
            return f"执行 DDL 查询时发生错误: {str(e)}"
        except Exception as e:
            session.rollback()
            return f"执行 DDL 查询时发生意外错误: {str(e)}"


@mcp.tool()
def run_dml_query(ctx: Context, raw_dml_sql: str) -> str:
    """Run a raw DDL query, like INSERT, UPDATE, DELETE, etc.
    Args:
        raw_dml_sql: The raw DDL SQL query to run.
    """
    engine = ctx.request_context.lifespan_context.engine
    with Session(engine) as session:
        try:
            result = session.execute(text(raw_dml_sql))
            session.commit()  # 提交事务以保存更改
            # 返回受影响的行数
            return f"DML 查询成功执行。影响行数: {result.rowcount}"
        except SQLAlchemyError as e:
            session.rollback()  # 回滚事务
            return f"执行 DML 查询时发生错误: {str(e)}"
        except Exception as e:
            session.rollback()
            return f"执行 DML 查询时发生意外错误: {str(e)}"


@mcp.tool()
def run_dcl_query(ctx: Context, raw_dcl_sql: str) -> str:
    """Run a raw DCL SQL query, like GRANT, REVOKE, etc.
    Args:
        raw_dcl_sql: The raw DDL SQL query to run.
    """
    engine = ctx.request_context.lifespan_context.engine
    with Session(engine) as session:
        try:
            session.execute(text(raw_dcl_sql))
            session.commit()  # 提交事务以使权限更改生效
            return "DCL 查询成功执行。"
        except SQLAlchemyError as e:
            session.rollback()  # 回滚事务
            return f"执行 DCL 查询时发生错误: {str(e)}"
        except Exception as e:
            session.rollback()
            return f"执行 DCL 查询时发生意外错误: {str(e)}"


@click.command()
@click.option("--dsn", "-d", type=str, help="Database connection string")
@click.option("-v", "--verbose", count=True)
def serve(dsn: str, verbose: bool):
    os.environ["DATABASE_URL"] = dsn
    mcp.run()


if __name__ == "__main__":
    serve()
