# PgSQL MCP Server

[![PyPI - Version](https://img.shields.io/pypi/v/pgsql-mcp-server)](https://pypi.org/project/pgsql-mcp-server/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pgsql-mcp-server)
[![Maintainability](https://qlty.sh/badges/c2b49b14-0c09-4a33-b545-52e81a2ccab5/maintainability.svg)](https://qlty.sh/gh/twn39/projects/pgsql-mcp-server)

**English** | [简体中文](./README_zh.md)

**A powerful tool server based on the Model Context Protocol (MCP), enabling interaction with PostgreSQL databases via MCP calls.**

---

## 🚀 Overview

This project is built on the `FastMCP` framework and leverages the `SQLAlchemy` and `asyncpg` libraries to deliver high-performance asynchronous database operations, ensuring efficiency and responsiveness when handling database requests.

## ✨ Key Features

- **Asynchronous & Efficient:** Fully asynchronous implementation based on `asyncio`, utilizing `asyncpg` for a high-performance asynchronous PostgreSQL driver.
- **Transactional Safety:** DDL, DML, and DCL operations are executed within transactions with error handling and rollback mechanisms.
- **Easy Deployment:** Start the server with a simple command line interface.

## 📦 Installation

Ensure you have Python 3.8+ installed. Installation via `uvx` is recommended:

```bash
uvx pgsql-mcp-server --dsn postgresql://user:password@localhost:5432/db
```

## 🔍 Preview and Debugging

You can use the official MCP Inspector tool to visually inspect the tools provided by this server, view their parameters and descriptions, and perform test calls directly.

```bash
npx @modelcontextprotocol/inspector uvx pgsql-mcp-server --dsn "postgresql://user:password@host:port/database"
```

This will start a local web service. Open the provided URL in your browser to begin debugging.

## 🧪 Testing

This project uses `pytest` for testing.

### Run all tests
```bash
uv run pytest
```

### Run unit tests only
```bash
uv run pytest tests/test_app.py
```

### Run integration tests only
Integration tests require a local PostgreSQL instance. They default to `localhost:5432/postgres`.
```bash
uv run pytest tests/test_integration.py
```

## 🤝 Contributing

Contributions are welcome! If you have suggestions for improvements, feature requests, or find any bugs, please feel free to:

1.  Open an [Issue](https://github.com/twn39/pgsql-mcp-server/issues) to discuss.
2.  Fork the repository and create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a [Pull Request](https://github.com/twn39/pgsql-mcp-server/pulls).
