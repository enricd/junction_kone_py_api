from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from schemas import InputData, OutputData
import tempfile
import os
import zipfile
import sys
import logging
import traceback
import json
# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import create_3d_building


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust allowed origins as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/status")
async def status():
    return {"status": "ok"}


@app.post("/build_3d_model")
async def build_3d_model(request: Request, background_tasks: BackgroundTasks):
    try:
        # Parse the JSON payload
        json_plan = await request.json()
        with open("../tmp/plan.json", "w") as f:
            json.dump(json_plan, f)
        logger.debug(f"Received plan: {json_plan}")

        response = create_3d_building(json_plan)
        output_data = OutputData(
            above_file=response["above_file"],
            under_file=response["under_file"],
            elevator_file=response["elevator_file"]
        )
        print_response = {k: (len(v) if v else None) for k, v in output_data.model_dump().items()}
        logger.info(f"Response: {print_response}")
        return output_data

    except Exception as e:
        logger.error(f"Error in build_3d_model endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )


