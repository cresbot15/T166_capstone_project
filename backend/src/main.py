from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import auth, groups, users, units
from src.database import engine, Base

# Make sure models definitely get imported
from src.models import user, group, unit

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

# Routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(groups.router, prefix="/groups", tags=["Groups"])
app.include_router(groups.router, prefix="/units", tags=["Units"])