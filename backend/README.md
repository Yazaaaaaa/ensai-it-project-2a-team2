
# Backend - Engine API

This is the core engine of the application. It is a layered REST API built with [FastAPI](https://fastapi.tiangolo.com/), responsible for game logic, player management, and data persistence.

## 🚀 Run the application

Command to run from the repository's root directory:

- Install all dependencies: `uv sync --project backend --all-extras`
  - option all-extras: including dev dependancies
- Launch the API in development mode: `uv run --project backend python backend/src/main.py`

:bulb: First Launch: Click on **Reset Database** to initialize it.

## 🏛️ Architecture

The backend follows a **Layered Architecture** (N-Tier) to ensure separation of concerns and maintainability:

- **Business Object** (`business_object/`) : Represents the pure domain entities
- **Controller** (`controller/`) : Handles HTTP requests and routing via FastAPI
- **Service** (`service/`) : Contains the core business logic
- **DAO** (`dao/`) : Manages database interactions
- **Schema** (`schema/`) : Data contract via [Pydantic](https://pydantic.dev/docs/validation/latest/get-started/) to ensure API requests and responses follow a strict structure

### Layers

Sequence diagram of the player retrieval flow through the application layers:

```mermaid
sequenceDiagram
    participant Client as Client
    participant Router as API Router (main)
    participant WS as PlayerController
    participant Service as PlayerService
    participant DAO as PlayerDao

    Client->>Router: GET /player/1
    Note right of Router: Route matching /player
    Router->>WS: player_by_id(id_player=1)

    WS->>Service: find_by_id(1)

    Service->>DAO: find_by_id(1)
    DAO-->>DAO: Database request <br/>SELECT *<br/>FROM player<br/> WHERE id = 1
    DAO-->>Service: Player instance (or None)
    Service-->>WS: Player instance (or None)
    WS-->>Client: 200 OK JSON {id_player: 1, username: "...", ...} <br/> or 404 Not Found
```

### Config files

In both the backend and frontend folders, you will find:

| Item                  | Description                                         | 
| --------------------- | --------------------------------------------------- | 
| logging_config.yml    | Configuration for the structured logging system.    | 
| pyproject.toml        | Project metadata and dependency definitions.        | 
| uv.lock               | Lockfile that ensures reproducible environments by pinning exact dependency versions. |
| \_\_init\_\_.py       | Marks a directory as a Python package, enabling module imports. |


## ⚒️ Development toolkit

### Debugging & Logs

The application uses a structured logging system. Logs are written to the `backend/logs/` directory and follow the format defined in `logging_config.yml`.

A custom `@log` decorator is available to automatically log method inputs and outputs, making it much easier to trace the flow of data through the services.

### Unit tests

To ensure tests are repeatable, safe, and **do not interfere with the real database**, we use a dedicated schema for unit testing.

The DAO unit tests use data from the `data/pop_db_test.sql` file.

This data is loaded into a separate schema (project_test_dao) so as not to pollute the other data.

- [ ] Lanch unit tests: `uv run --project backend pytest -v` 

It is also possible to generate test coverage using [Coverage](https://coverage.readthedocs.io/en/)

- [ ] `uv run --project backend coverage run -m pytest backend`
- [ ] `uv run --project backend coverage report -m`
- [ ] `uv run --project backend coverage html`
  - Download and open coverage_report/index.html

### Ruff

The **format on save** with [Ruff](https://docs.astral.sh/ruff/) is enabled by default in the workspace (cf. *.vscode/settings.json*).

To do it manually:

- ensures consistent and readable code style: `uv run --project backend ruff format backend/`
- identifies and fixes potential issues: `uv run --project frontend ruff check --fix backend/`


### Pylint

Static analysis with **pylint**: `uv run --project backend --extra dev pylint --output-format=colorized --disable=C0114,C0411,C0415,W0718 $(git ls-files 'backend/**/*.py') --fail-under=7.5`