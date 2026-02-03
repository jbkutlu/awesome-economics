import yaml
import json
from pydantic import BaseModel, HttpUrl
from datetime import date
from typing import List

# 1. Define Data Schema (Prevents mistakes)
class Event(BaseModel):
    title: str
    date: date
    type: str  # Conference, Competition, etc.
    link: HttpUrl
    location: str

# 2. Read from YAML
with open("events.yaml", "r") as f:
    raw_data = yaml.safe_load(f)

# 3. Validate Data and Convert to JSON
validated_events = [Event(**e).model_dump() for e in raw_data]

with open("events.json", "w") as f:
    json.dump(validated_events, f, default=str)