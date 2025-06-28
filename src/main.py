from fastapi import FastAPI
from routes import base_router, diy_router, image_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],               # allow all origins
    allow_credentials=False,           # optional: allows cookies/auth headers if needed
    allow_methods=["*"],              # allow all HTTP methods (GET, POST, PUT, etc.)
    allow_headers=["*"],              # allow all request headers
)
app.include_router(base_router)
app.include_router(diy_router)
app.include_router(image_router)

@app.get("/")
async def test():
    return{
        "message":"Testinggg"
    }