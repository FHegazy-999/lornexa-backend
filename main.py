from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import date
import os
from sqlalchemy import create_engine, Column, Integer, String, Date, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration - Use SQLite for testing (no PostgreSQL needed!)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./lornexa.db")

# SQLAlchemy setup with SQLite configuration
if DATABASE_URL.startswith("sqlite"):
    # SQLite requires check_same_thread=False
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
else:
    # For PostgreSQL (when you're ready)
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Create FastAPI app
app = FastAPI(title="Lornexa Backend", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your Flutter app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class ProfileCreate(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    gender: Optional[str] = None
    country: Optional[str] = None
    ethnicity: Optional[str] = None
    marital_status: Optional[str] = None
    date_of_birth: Optional[str] = None
    autistic: Optional[str] = None

class ProfileResponse(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None  # Fixed: Changed from str to Optional[str]
    gender: Optional[str] = None     # Fixed: Changed from str to Optional[str]
    country: Optional[str] = None    # Fixed: Changed from str to Optional[str]
    ethnicity: Optional[str] = None  # Fixed: Changed from str to Optional[str]
    marital_status: Optional[str] = None  # Fixed: Changed from str to Optional[str]
    date_of_birth: Optional[str] = None  # Fixed: Changed from str to Optional[str]
    autistic: Optional[str] = None  # Fixed: Changed from str to Optional[str]
    
    class Config:
        from_attributes = True

# SQLAlchemy model - Keeping Date and Boolean imports though using String
class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    country = Column(String, nullable=True)
    ethnicity = Column(String, nullable=True)
    marital_status = Column(String, nullable=True)
    date_of_birth = Column(String, nullable=True)  # Storing as string in format "DD/MM/YYYY"
    autistic = Column(String, nullable=True)

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    db_type = "SQLite" if DATABASE_URL.startswith("sqlite") else "PostgreSQL"
    return {"message": "Lornexa Backend API", "status": "running", "database": db_type}

@app.post("/api/profiles", response_model=ProfileResponse)
def create_profile(profile: ProfileCreate):
    db = SessionLocal()
    try:
        # Create new profile
        db_profile = Profile(
            first_name=profile.first_name,
            last_name=profile.last_name,
            gender=profile.gender,
            country=profile.country,
            ethnicity=profile.ethnicity,
            marital_status=profile.marital_status,
            date_of_birth=profile.date_of_birth,
            autistic=profile.autistic
        )
        
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)
        
        return db_profile
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/profiles/{profile_id}", response_model=ProfileResponse)
def get_profile(profile_id: int):
    db = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.id == profile_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile
    finally:
        db.close()

@app.get("/api/profiles", response_model=list[ProfileResponse])
def get_all_profiles():
    db = SessionLocal()
    try:
        profiles = db.query(Profile).all()
        return profiles
    finally:
        db.close()

@app.put("/api/profiles/{profile_id}", response_model=ProfileResponse)
def update_profile(profile_id: int, profile: ProfileCreate):
    db = SessionLocal()
    try:
        db_profile = db.query(Profile).filter(Profile.id == profile_id).first()
        if not db_profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Update fields
        for key, value in profile.dict().items():
            setattr(db_profile, key, value)
        
        db.commit()
        db.refresh(db_profile)
        
        return db_profile
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.delete("/api/profiles/{profile_id}")
def delete_profile(profile_id: int):
    db = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.id == profile_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        db.delete(profile)
        db.commit()
        
        return {"message": "Profile deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    db_type = "SQLite" if DATABASE_URL.startswith("sqlite") else "PostgreSQL"
    print(f"🚀 Starting Lornexa Backend with {db_type}")
    print(f"📡 API: http://localhost:8000")
    print(f"📚 Docs: http://localhost:8000/docs")
    uvicorn.run("__main__:app", host="0.0.0.0", port=8000, reload=True)