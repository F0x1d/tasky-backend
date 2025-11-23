from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
import math
import os

from .database import get_db, init_db
from .models import Task
from .schemas import TaskCreate, TaskUpdate, TaskResponse, PaginatedTasksResponse
from .auth import get_current_user_id

app = FastAPI(
    title="Tasks Service",
    description="Tasks management microservice with pagination",
    version="1.0.0",
    root_path=os.getenv("API_PATH", ""),
)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "tasks_requests_total", "Total requests", ["method", "endpoint", "status"]
)
REQUEST_DURATION = Histogram(
    "tasks_request_duration_seconds", "Request duration", ["method", "endpoint"]
)


@app.middleware("http")
async def prometheus_middleware(request, call_next):
    """Middleware to collect Prometheus metrics"""
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    REQUEST_COUNT.labels(
        method=request.method, endpoint=request.url.path, status=response.status_code
    ).inc()
    REQUEST_DURATION.labels(method=request.method, endpoint=request.url.path).observe(
        duration
    )

    return response


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint"""
    return {"service": "tasks-service", "status": "running"}


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Tasks"],
)
async def create_task(
    task_data: TaskCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new task"""
    new_task = Task(user_id=user_id, title=task_data.title, content=task_data.content)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@app.get("/tasks", response_model=PaginatedTasksResponse, tags=["Tasks"])
async def get_tasks(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get paginated list of user tasks"""
    # Calculate offset
    offset = (page - 1) * page_size

    # Get total count
    total = db.query(func.count(Task.id)).filter(Task.user_id == user_id).scalar()

    # Get tasks with pagination
    tasks = (
        db.query(Task)
        .filter(Task.user_id == user_id)
        .order_by(Task.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    # Calculate total pages
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return PaginatedTasksResponse(
        tasks=tasks,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
async def get_task(
    task_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get a specific task by ID"""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


@app.put("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update a task"""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    # Update fields if provided
    if task_data.title is not None:
        task.title = task_data.title
    if task_data.content is not None:
        task.content = task_data.content

    db.commit()
    db.refresh(task)
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Tasks"])
async def delete_task(
    task_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a task"""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    db.delete(task)
    db.commit()
    return None
