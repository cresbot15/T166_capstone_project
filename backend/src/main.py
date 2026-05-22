from fastapi import FastAPI
from src.routers import auth
from src.database import engine, Base

# Make sure the models definitely get imported before creating db
from src.models import user, group

app = FastAPI()

# Database connection creation
Base.metadata.create_all(bind=engine)

# Routes
app.include_router(auth.router, prefix = "/auth", tags=["Authentication"])