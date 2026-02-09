# PgSQL MCP Server

[![PyPI - Version](https://img.shields.io/pypi/v/pgsql-mcp-server)](https://pypi.org/project/pgsql-mcp-server/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pgsql-mcp-server)
[![Maintainability](https://qlty.sh/badges/c2b49b14-0c09-4a33-b545-52e81a2ccab5/maintainability.svg)](https://qlty.sh/gh/twn39/projects/pgsql-mcp-server)

[English](./README.md) | **简体中文**

**基于 Model Context Protocol (MCP) 的强大工具服务器，允许通过 MCP 调用与 PostgreSQL 数据库进行交互。**

---

## 🚀 概述

该项目基于 `FastMCP` 框架，并利用 `SQLAlchemy` 和 `asyncpg` 库来提供高性能的异步数据库操作，确保在处理数据库请求时具有高效性和响应性。

## ✨ 主要特性

- **异步且高效：** 基于 `asyncio` 的完全异步实现，使用 `asyncpg` 作为高性能异步 PostgreSQL 驱动。
- **事务安全：** DDL、DML 和 DCL 操作都在事务中执行，并具有错误处理和回滚机制。
- **易于部署：** 通过简单的命令行界面启动服务器。

## 📦 安装

确保您已安装 Python 3.10+。推荐方式：

### 使用 uv (推荐)

```bash
uv tool install pgsql-mcp-server
```

然后运行：
```bash
pgsql-mcp-server --dsn "postgresql://user:password@localhost:5432/db"
```

或者不安装直接运行：
```bash
uvx pgsql-mcp-server --dsn "postgresql://user:password@localhost:5432/db"
```

### 使用 pip

```bash
pip install pgsql-mcp-server
```

## 🛠️ 可用工具

该服务器提供以下工具用于数据库交互：

- **`get_schema_names`**: 列出数据库中的所有模式。
- **`get_tables`**: 列出特定模式中的所有表（默认为 `public`）。
- **`get_columns`**: 获取特定表的详细列信息。
- **`get_indexes`**: 获取特定表的索引详情。
- **`get_foreign_keys`**: 获取特定表的外键约束。
- **`run_dql_query`**: 执行数据查询语言 (DQL) 语句，如 `SELECT`, `SHOW`, `EXPLAIN`。
- **`run_dml_query`**: 执行数据操作语言 (DML) 语句，如 `INSERT`, `UPDATE`, `DELETE`。
- **`run_ddl_query`**: 执行数据定义语言 (DDL) 语句，如 `CREATE`, `ALTER`, `DROP`。
- **`run_dcl_query`**: 执行数据控制语言 (DCL) 语句，如 `GRANT`, `REVOKE`。


## 🔍 预览与调试

您可以使用官方的 MCP Inspector 工具直观地查看此服务器提供的工具，查看它们的参数和描述，并直接进行测试调用。

```bash
npx @modelcontextprotocol/inspector uvx pgsql-mcp-server --dsn "postgresql://user:password@host:port/database"
```

这将会启动一个本地 Web 服务。在浏览器中打开提供的 URL 即可开始调试。

## 🧪 测试

本项目使用 `pytest` 进行测试。

### 运行所有测试
```bash
uv run pytest
```

### 仅运行单元测试
```bash
uv run pytest tests/test_app.py
```

### 仅运行集成测试
集成测试需要本地 PostgreSQL 实例。默认连接地址为 `localhost:5432/postgres`。
```bash
uv run pytest tests/test_integration.py
```

## 🤝 贡献代码

欢迎贡献代码！如果您有任何改进建议、功能请求或发现任何错误，请随时：

1.  提交 [Issue](https://github.com/twn39/pgsql-mcp-server/issues) 进行讨论。
2.  Fork 该仓库并创建您的特性分支 (`git checkout -b feature/AmazingFeature`)。
3.  提交您的更改 (`git commit -m 'Add some AmazingFeature'`)。
4.  推送到该分支 (`git push origin feature/AmazingFeature`)。
5.  提交 [Pull Request](https://github.com/twn39/pgsql-mcp-server/pulls)。
