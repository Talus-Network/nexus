from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class ModelDetail(BaseModel):
    format: str
    family: str
    families: Optional[List[str]] = None
    parameter_size: str
    quantization_level: str


class Model(BaseModel):
    name: str
    modified_at: datetime
    size: int
    digest: str
    details: ModelDetail


class ModelsResponse(BaseModel):
    models: List[Model]
