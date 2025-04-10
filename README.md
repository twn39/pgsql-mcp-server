
## Run MCP Server

```shell
uvx pgsql-mcp-server --dsn postgresql+psycopg2://postgres:postgres@localhost:5432/db
```


## Preview or debug 

``` 
npx @modelcontextprotocol/inspector pgsql-mcp-server --dsn postgresql+psycopg2://postgres:postgres@localhost:5432/db
```