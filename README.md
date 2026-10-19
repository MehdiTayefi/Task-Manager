# Task Manager API

A personal task management REST API built with Django and Django REST Framework.

This project focuses on authentication, serializers, permissions,
queryset filtering, and automated API testing.

## Tech Stack

- Python
- Django
- Django REST Framework
- Simple JWT
- django-filter
- Django Unfold
- SQLite for local development

## Features

### Authentication and Accounts

- User registration with password validation and hashing
- JWT login with access and refresh tokens
- Refresh token rotation and blacklisting
- Logout by revoking the submitted refresh token
- Current user profile
- Account deletion with current password confirmation
- Refresh token revocation when a user is deleted through the API or admin

### Tasks

- Create, list, retrieve, update, and delete tasks
- Restrict task access to the owner
- Filter by status and priority
- Pagination with 10 tasks per page
- Newest tasks first

## Local Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Linux / macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and configure:

```dotenv
DJANGO_SECRET_KEY="your-generated-secret-key"
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

Generate a secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Apply migrations and start the server:

```bash
python manage.py migrate
python manage.py runserver
```

## API Endpoints

Base URL: `/api/v1/`

| Method | Endpoint | Description |
| -------- | ---------- | ------------- |
| POST | `auth/register/` | Register a user |
| POST | `auth/login/` | Obtain access and refresh tokens |
| POST | `auth/refresh/` | Rotate refresh and obtain new tokens |
| POST | `auth/logout/` | Revoke the submitted refresh token |
| GET | `users/me/` | Retrieve the current user |
| DELETE | `users/me/` | Delete the current account |
| GET | `tasks/` | List the current user's tasks |
| POST | `tasks/` | Create a task |
| GET | `tasks/{id}/` | Retrieve a task |
| PATCH | `tasks/{id}/` | Partially update a task |
| DELETE | `tasks/{id}/` | Delete a task |

Protected endpoints require:

```http
Authorization: Bearer <access_token>
```

Refresh and logout requests require a `refresh` field in the JSON body.
Account deletion requires a `password` field.

## Task Fields

| Field | Description |
| ------- | ------------- |
| `title` | Required title, up to 200 characters |
| `description` | Optional description |
| `status` | `todo`, `in_progress`, or `done` |
| `priority` | `low`, `medium`, or `high` |
| `due_date` | Optional date in `YYYY-MM-DD` format |
| `owner` | Assigned by the server |
| `created_at` | Creation timestamp |
| `updated_at` | Last update timestamp |

Example request:

```json
{
  "title": "Practice Django serializers",
  "description": "Review validation and read-only fields",
  "status": "todo",
  "priority": "high"
}
```

Example filtering:

```http
GET /api/v1/tasks/?status=todo&priority=high&page=1
```

## Authentication Behavior

- Access tokens expire after 5 minutes.
- Refresh tokens expire after 7 days.
- Refresh rotation issues a new refresh token and blacklists the previous one.
- Clients must replace the stored refresh token after each successful refresh.
- Logout revokes only the submitted refresh token.
- Logout does not immediately invalidate an existing access token.
- Deleted or inactive users cannot access protected endpoints or refresh tokens.
- Requests for another user's task return `404`.

## Admin

The admin interface uses Django Unfold.

Create an administrator:

```bash
python manage.py createsuperuser
```

Admin URL: `http://127.0.0.1:8000/admin/`

## Tests

Run the API tests:

```bash
python manage.py test accounts tasks --verbosity 2
```

Tests cover registration, password hashing, JWT rotation, logout,
account deletion, admin deletion, task ownership, filtering, and pagination.

## Project Status

The backend API is implemented. Frontend development is planned.