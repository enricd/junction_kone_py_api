# create a simple fastapi app that sends a json with 3 stl or glb files that could be None

import requests
import fastapi
import uvicorn

app = fastapi.FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.post("/build_3d_model")
def build_3d_model(json_plan: dict):
    return {"message": "3D model built successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
