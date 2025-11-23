# Tasks Service - Agent Guidelines

## Commands
- **Run app**: `uv run uvicorn app.main:app --host 0.0.0.0 --port 8001`
- **Run single test**: No test suite configured yet
- **Dependencies**: `uv sync` (install), `uv add <package>` (add new)

## Code Style
- **Python version**: 3.13 (use modern syntax)
- **Imports**: stdlib, then third-party, then local (`.app` relative imports)
- **Type hints**: Required - use modern union syntax `str | None` (not `Optional`)
- **Strings**: Double quotes `""`
- **Async**: Use `async def` for all FastAPI endpoints
- **Pydantic**: Use `Field(...)` for validation, `model_config` for settings
- **SQLAlchemy**: Declarative Base, use proper type hints on columns
- **Docstrings**: Triple-quoted strings for all functions/classes

## Error Handling
- Use FastAPI `HTTPException` with proper status codes
- Always include `detail` parameter in exceptions
- Return proper HTTP status codes (201 for create, 204 for delete, 404 for not found)

## Project Structure
- `app/main.py` - FastAPI routes and app initialization
- `app/models.py` - SQLAlchemy models
- `app/schemas.py` - Pydantic schemas for request/response
- `app/auth.py` - JWT authentication with RSA public key
- `app/config.py` - Settings using pydantic-settings
- `app/database.py` - SQLAlchemy engine and session management
