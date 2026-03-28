"""High School Management System API.

Includes role-based authentication and protected registration actions.
"""

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
import os
from pathlib import Path

from database import Base, engine, get_db, SessionLocal
import models

# Create all tables (no-op when they already exist)
Base.metadata.create_all(bind=engine)

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

# ---------------------------------------------------------------------------
# Default seed data
# ---------------------------------------------------------------------------

_DEFAULT_ACTIVITIES = [
    {
        "name": "Chess Club",
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    },
    {
        "name": "Programming Class",
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
    },
    {
        "name": "Gym Class",
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"],
    },
    {
        "name": "Soccer Team",
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"],
    },
    {
        "name": "Basketball Team",
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"],
    },
    {
        "name": "Art Club",
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"],
    },
    {
        "name": "Drama Club",
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"],
    },
    {
        "name": "Math Club",
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"],
    },
    {
        "name": "Debate Team",
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"],
    },
]


def _seed_database(db: Session) -> None:
    """Seed the database with default activities and users if empty."""
    # Seed activities
    if db.query(models.Activity).count() == 0:
        for data in _DEFAULT_ACTIVITIES:
            activity = models.Activity(
                name=data["name"],
                description=data["description"],
                schedule=data["schedule"],
                max_participants=data["max_participants"],
            )
            db.add(activity)
            db.flush()  # assign primary key before adding participants
            for email in data["participants"]:
                db.add(models.Participant(activity_name=activity.name, email=email))
        db.commit()

    # Seed default users
    if db.query(models.User).count() == 0:
        defaults = [
            {"username": "admin1", "email": "admin1@mergington.edu", "role": "admin"},
            {"username": "faculty1", "email": "faculty1@mergington.edu", "role": "faculty"},
            {"username": "coordinator1", "email": "coordinator1@mergington.edu", "role": "coordinator"},
            {"username": "student1", "email": "student1@mergington.edu", "role": "student"},
        ]
        for u in defaults:
            db.add(models.User(
                username=u["username"],
                email=u["email"],
                password_hash=pwd_context.hash("ChangeMe123!"),
                role=u["role"],
            ))
        db.commit()


# Run seed on startup
with SessionLocal() as _startup_db:
    _seed_database(_startup_db)

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


def get_current_user(request: Request, db: Session = Depends(get_db)) -> dict:
    username = request.session.get("username")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return {"username": user.username, "email": user.email, "role": user.role,
            "password_hash": user.password_hash}


def require_roles(*allowed_roles: str):
    def role_dependency(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of: {', '.join(allowed_roles)}"
            )
        return user

    return role_dependency

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities(db: Session = Depends(get_db)):
    activities = db.query(models.Activity).all()
    return {
        activity.name: {
            "description": activity.description,
            "schedule": activity.schedule,
            "max_participants": activity.max_participants,
            "participants": [p.email for p in activity.participants],
        }
        for activity in activities
    }


@app.post("/auth/register")
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    db.add(models.User(
        username=payload.username,
        email=payload.email,
        password_hash=pwd_context.hash(payload.password),
        role="student",
    ))
    db.commit()
    return {"message": "Registration successful", "role": "student"}


@app.post("/auth/login")
def login_user(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == payload.username).first()
    if not user or not pwd_context.verify(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    request.session["username"] = payload.username
    return {
        "message": "Login successful",
        "username": payload.username,
        "role": user.role,
    }


@app.post("/auth/logout")
def logout_user(request: Request):
    request.session.clear()
    return {"message": "Logged out successfully"}


@app.get("/auth/me")
def get_me(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if not username:
        return {"authenticated": False}

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        request.session.clear()
        return {"authenticated": False}

    return {
        "authenticated": True,
        "username": user.username,
        "email": user.email,
        "role": user.role,
    }


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("admin", "faculty", "coordinator")),
):
    """Sign up a student for an activity"""
    activity = db.query(models.Activity).filter_by(name=activity_name).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    already_signed = db.query(models.Participant).filter_by(
        activity_name=activity_name,
        email=email,
    ).first()
    if already_signed:
        raise HTTPException(status_code=400, detail="Student is already signed up")

    db.add(models.Participant(activity_name=activity_name, email=email))
    db.commit()
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("admin", "faculty", "coordinator")),
):
    """Unregister a student from an activity"""
    activity = db.query(models.Activity).filter_by(name=activity_name).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    participant = db.query(models.Participant).filter_by(
        activity_name=activity_name,
        email=email,
    ).first()
    if not participant:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    db.delete(participant)
    db.commit()
    return {"message": f"Unregistered {email} from {activity_name}"}
