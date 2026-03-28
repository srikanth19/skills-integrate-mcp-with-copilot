"""High School Management System API.

Includes role-based authentication and protected registration actions.
"""

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from starlette.middleware.sessions import SessionMiddleware
import os
import json
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", "dev-only-change-me"),
    same_site="lax"
)

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
USERS_FILE = current_dir / "users.json"


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


def _seed_default_users() -> dict:
    """Seed users if none exist yet.

    Default password for all seeded users: ChangeMe123!
    """
    defaults = {
        "admin1": {
            "email": "admin1@mergington.edu",
            "password_hash": pwd_context.hash("ChangeMe123!"),
            "role": "admin"
        },
        "faculty1": {
            "email": "faculty1@mergington.edu",
            "password_hash": pwd_context.hash("ChangeMe123!"),
            "role": "faculty"
        },
        "coordinator1": {
            "email": "coordinator1@mergington.edu",
            "password_hash": pwd_context.hash("ChangeMe123!"),
            "role": "coordinator"
        },
        "student1": {
            "email": "student1@mergington.edu",
            "password_hash": pwd_context.hash("ChangeMe123!"),
            "role": "student"
        }
    }
    with USERS_FILE.open("w", encoding="utf-8") as f:
        json.dump(defaults, f, indent=2)
    return defaults


def _load_users() -> dict:
    if not USERS_FILE.exists():
        return _seed_default_users()

    with USERS_FILE.open("r", encoding="utf-8") as f:
        users = json.load(f)

    # If placeholder hashes are present, re-seed file with valid bcrypt hashes.
    if any(str(data.get("password_hash", "")).startswith("$2b$12$placeholder") for data in users.values()):
        return _seed_default_users()

    return users


def _save_users(users: dict) -> None:
    with USERS_FILE.open("w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def get_current_user(request: Request) -> dict:
    username = request.session.get("username")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    users = _load_users()
    user = users.get(username)
    if not user:
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return {"username": username, **user}


def require_roles(*allowed_roles: str):
    def role_dependency(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of: {', '.join(allowed_roles)}"
            )
        return user

    return role_dependency

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/auth/register")
def register_user(payload: RegisterRequest):
    users = _load_users()

    if payload.username in users:
        raise HTTPException(status_code=400, detail="Username already exists")

    if any(u.get("email") == payload.email for u in users.values()):
        raise HTTPException(status_code=400, detail="Email already exists")

    users[payload.username] = {
        "email": payload.email,
        "password_hash": pwd_context.hash(payload.password),
        "role": "student"
    }
    _save_users(users)
    return {"message": "Registration successful", "role": "student"}


@app.post("/auth/login")
def login_user(payload: LoginRequest, request: Request):
    users = _load_users()
    user = users.get(payload.username)
    if not user or not pwd_context.verify(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    request.session["username"] = payload.username
    return {
        "message": "Login successful",
        "username": payload.username,
        "role": user["role"]
    }


@app.post("/auth/logout")
def logout_user(request: Request):
    request.session.clear()
    return {"message": "Logged out successfully"}


@app.get("/auth/me")
def get_me(request: Request):
    username = request.session.get("username")
    if not username:
        return {"authenticated": False}

    users = _load_users()
    user = users.get(username)
    if not user:
        request.session.clear()
        return {"authenticated": False}

    return {
        "authenticated": True,
        "username": username,
        "email": user["email"],
        "role": user["role"]
    }


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str,
    _: dict = Depends(require_roles("admin", "faculty", "coordinator"))
):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str,
    _: dict = Depends(require_roles("admin", "faculty", "coordinator"))
):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
