import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional
from dataclasses import dataclass
from sqlmodel import create_engine, Session, text
from sqlalchemy.engine import Engine
from mcp.server.fastmcp import FastMCP, Context
from dotenv import load_dotenv
from sqlalchemy import inspect

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "错误：请设置 DATABASE_URL 环境变量。格式：postgresql+psycopg2://user:password@host:port/database"
    )


@dataclass
class AppContext:
    engine: Engine


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    engine = create_engine(DATABASE_URL, echo=False)

    try:
        with Session(engine) as session:
            session.execute(text("SELECT 1"))
    except Exception as e:
        raise RuntimeError(
            f"无法连接到数据库，请检查 DATABASE_URL 和数据库状态: {e}"
        ) from e

    try:
        yield AppContext(engine=engine)
    finally:
        engine.dispose()


mcp = FastMCP("PostgreSQL Schema Explorer", lifespan=app_lifespan)

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
def get_tables_in_schema(ctx: Context, schema_name: Optional[str] = "public") -> str:
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
        error_message = f"查询表时发生错误: {str(e)}"
        return error_message


if __name__ == "__main__":
    mcp.run()
