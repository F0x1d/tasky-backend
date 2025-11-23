# API Documentation

## Auth Service API

Base URL: `https://yourdomain.com/auth`

### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "username": "testuser",
  "password": "password123"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "username": "testuser",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Get Current User
```http
GET /auth/me
Authorization: Bearer <ACCESS_TOKEN>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "testuser",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

---

## Tasks Service API

Base URL: `https://yourdomain.com/tasks`

All endpoints require authentication via Bearer token.

### Create Task
```http
POST /tasks/tasks
Authorization: Bearer <ACCESS_TOKEN>
Content-Type: application/json

{
  "title": "My Task",
  "content": "Task description here"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "user_id": 1,
  "title": "My Task",
  "content": "Task description here",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

### Get Tasks (Paginated)
```http
GET /tasks/tasks?page=1&page_size=10
Authorization: Bearer <ACCESS_TOKEN>
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (1-100, default: 10)

**Response (200 OK):**
```json
{
  "tasks": [
    {
      "id": 1,
      "user_id": 1,
      "title": "My Task",
      "content": "Task description here",
      "created_at": "2024-01-01T12:00:00",
      "updated_at": "2024-01-01T12:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}
```

### Get Single Task
```http
GET /tasks/tasks/{task_id}
Authorization: Bearer <ACCESS_TOKEN>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 1,
  "title": "My Task",
  "content": "Task description here",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

### Update Task
```http
PUT /tasks/tasks/{task_id}
Authorization: Bearer <ACCESS_TOKEN>
Content-Type: application/json

{
  "title": "Updated Task Title",
  "content": "Updated task description"
}
```

**Note:** Both `title` and `content` are optional. You can update only one field.

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 1,
  "title": "Updated Task Title",
  "content": "Updated task description",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:30:00"
}
```

### Delete Task
```http
DELETE /tasks/tasks/{task_id}
Authorization: Bearer <ACCESS_TOKEN>
```

**Response (204 No Content)**

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Username already registered"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 404 Not Found
```json
{
  "detail": "Task not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "username"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Complete Example: Create and Manage Tasks

### 1. Register a new user
```bash
curl -X POST https://yourdomain.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "password": "securepass123"}'
```

### 2. Login to get tokens
```bash
curl -X POST https://yourdomain.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "password": "securepass123"}'
```

Save the `access_token` from the response.

### 3. Create a task
```bash
curl -X POST https://yourdomain.com/tasks/tasks \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy groceries", "content": "Milk, eggs, bread"}'
```

### 4. Get all tasks
```bash
curl -X GET "https://yourdomain.com/tasks/tasks?page=1&page_size=10" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### 5. Update a task
```bash
curl -X PUT https://yourdomain.com/tasks/tasks/1 \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy groceries", "content": "Milk, eggs, bread, cheese"}'
```

### 6. Delete a task
```bash
curl -X DELETE https://yourdomain.com/tasks/tasks/1 \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

---

## OpenAPI Documentation

Interactive API documentation is available at:
- Auth Service: `https://yourdomain.com/auth/docs`
- Tasks Service: `https://yourdomain.com/tasks/docs`

You can test all endpoints directly from the browser using the Swagger UI.

**Note:** Replace `yourdomain.com` with your actual domain configured in Cloudflare DNS.
