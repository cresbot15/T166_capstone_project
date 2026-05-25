from fastapi import FastAPI
from src.routers import auth, groups, users
from src.database import engine, Base

# Make sure models definitely get imported
from src.models import user, group

app = FastAPI()

Base.metadata.create_all(bind=engine)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(groups.router, prefix="/groups", tags=["Groups"])