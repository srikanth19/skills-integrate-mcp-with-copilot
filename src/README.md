# Mergington High School Activities API

A FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- Role-based authentication (admin, faculty, coordinator, student)
- Persistent storage via a MySQL (or SQLite) database

## Getting Started

1. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

2. *(Optional)* Configure the database URL. By default the app uses a local
   SQLite file (`activities.db`). To use MySQL, set the `DATABASE_URL`
   environment variable before starting:

   ```
   export DATABASE_URL="mysql+pymysql://user:password@host:3306/dbname"
   ```

3. Run the application:

   ```
   python app.py
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## Database Configuration

| Variable       | Default                          | Description                                   |
| -------------- | -------------------------------- | --------------------------------------------- |
| `DATABASE_URL` | `sqlite:///./activities.db`      | SQLAlchemy connection URL for MySQL or SQLite  |
| `SESSION_SECRET` | `dev-only-change-me`           | Secret key used to sign session cookies        |

The application creates all required tables automatically on first startup and
seeds them with default activities and users (password: `ChangeMe123!`).

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity (requires admin/faculty/coordinator role)   |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Remove a student from an activity (requires admin/faculty/coordinator role) |
| POST   | `/auth/register`                                                  | Register a new student account                                      |
| POST   | `/auth/login`                                                     | Log in and receive a session cookie                                 |
| POST   | `/auth/logout`                                                    | Log out                                                             |
| GET    | `/auth/me`                                                        | Get the currently authenticated user                                |

## Data Model

The application uses a relational database with the following tables:

1. **activities** — one row per extracurricular activity:
   - `name` (primary key) — activity name
   - `description`
   - `schedule`
   - `max_participants`

2. **participants** — student enrolment (many-to-many via join table):
   - `id` (auto-increment primary key)
   - `activity_name` (foreign key → activities)
   - `email` — student email address

3. **users** — system accounts:
   - `username` (primary key)
   - `email`
   - `password_hash`
   - `role` — one of `admin`, `faculty`, `coordinator`, `student`

Data is persisted across application restarts in the configured database.
