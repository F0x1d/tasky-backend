# Agent Guidelines for auth-service

## Commands
- Run server: `uv run uvicorn app.main:app --reload`
- Install deps: `uv sync`
- Add package: `uv add <package>`
- Run tests: `uv run pytest tests/` (single test: `pytest tests/test_file.py::test_function`)

## Code Style
- **Python**: 3.13+, FastAPI, SQLAlchemy ORM, Pydantic v2
- **Imports**: Group stdlib, third-party, local with blank lines between. Use relative imports for local modules (from .module import)
- **Types**: Always use type hints on function params and returns (use Optional[T], not T | None)
- **Naming**: snake_case for functions/vars, PascalCase for classes
- **Docstrings**: Triple quotes for all functions
- **Models**: Pydantic BaseModel for schemas, SQLAlchemy Base for DB models
- **Config**: Use pydantic_settings BaseSettings with model_config
- **Error handling**: Raise HTTPException with explicit status codes from fastapi.status
- **Validation**: Use Pydantic Field() with constraints (min_length, max_length, etc.)
- **DB sessions**: Use Depends(get_db) for dependency injection
- **Auth**: JWT RSA tokens (access + refresh), use HTTPBearer security scheme
