from pydantic import BaseModel
from datetime import datetime
class Location(BaseModel):
    x: float
    y: float

class UserContext(BaseModel):
    time: datetime
    location: Location
