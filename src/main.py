from fastapi import FastAPI
from routes import base_router, diy_router

app = FastAPI()

app.include_router(base_router)
app.include_router(diy_router)

@app.get("/")
async def test():
    return{
        "message":"Testinggg"
    }