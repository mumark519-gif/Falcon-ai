from fastapi import FastAPI


from app.api.chat import router as chat_router
from app.api.auth import router as auth_router
from app.api.memory import router as memory_router
from app.api.business import router as business_router
from app.database import engine
from app.models import Base
import app.models


app = FastAPI()

app.include_router(auth_router)
app.include_router(business_router)
app.include_router(chat_router)
app.include_router(memory_router)

print(Base.metadata.tables.keys())
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Welcome to Falcon AI!"}
