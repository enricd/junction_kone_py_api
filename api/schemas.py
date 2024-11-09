from pydantic import BaseModel
from typing import Optional

class InputData(BaseModel):
    json_plan: dict  # Define the structure of your input JSON here

class OutputData(BaseModel):
    above_file: Optional[str] = None
    under_file: Optional[str] = None
    elevator_file: Optional[str] = None