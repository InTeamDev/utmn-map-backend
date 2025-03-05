from datetime import datetime

from pydantic import BaseModel


class Location(BaseModel):
    x: float
    y: float


class UserContext(BaseModel):
    time: datetime
    location: Location
