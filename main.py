import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional
from dataclasses import dataclass
from sqlmodel import create_engine, Session, text
from sqlalchemy.engine import Engine
from mcp.server.fastmcp import FastMCP, Context
from dotenv import load_dotenv

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
def list_tables_in_schema(schema_name: Optional[str], ctx: Context) -> str:
    """Get all tables in a schema.

    Args:
        schema_name: The name of the schema to get tables from.
    """
    try:
        engine = ctx.request_context.lifespan_context.engine

        with Session(engine) as session:
            query = text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = :schema_name
                  AND table_type = 'BASE TABLE'
                ORDER BY table_name;
                """
            )
            result = session.execute(query, {"schema_name": schema_name})
            tables = [row[0] for row in result.fetchall()]

            if not tables:
                schema_exists_query = text(
                    "SELECT 1 FROM information_schema.schemata WHERE schema_name = :schema_name"
                )
                schema_result = session.execute(
                    schema_exists_query, {"schema_name": schema_name}
                )
                if not schema_result.first():
                    return f"错误：指定的 Schema '{schema_name}' 不存在。"
                else:
                    return f"在 Schema '{schema_name}' 中没有找到任何表。"
            else:
                return f"All tables from schema {schema_name}: {', '.join(tables)}"
    except Exception as e:
        error_message = f"查询表时发生错误: {str(e)}"
        return error_message


if __name__ == "__main__":
    mcp.run()
