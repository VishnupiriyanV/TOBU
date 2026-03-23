from pydantic import BaseModel, Field, constr
from typing import List, Optional, Generic, TypeVar, Literal, Union


try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

T = TypeVar('T')

class ErrorBody(BaseModel):
    code: str
    message: str

class EnvelopeSuccess(BaseModel, Generic[T]):
    ok: Literal[True] = True
    data: T

class EnvelopeError(BaseModel):
    ok: Literal[False] = False
    error: ErrorBody

class HybridSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=20, ge=1, le=200)
    semantic_limit: int = Field(default=40, ge=1, le=500)
    keyword_limit: int = Field(default=40, ge=1, le=500)
    k: int = Field(default=60, ge=1, le=200)
    source_types: Optional[List[str]] = None
    folders: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    min_score: float = Field(default=0.0, ge=0.0)

class HybridResultItem(BaseModel):
    file_name: Optional[str] = None
    file_path: str
    start: Optional[Union[float, int]] = None
    end: Optional[Union[float, int]] = None
    text: Optional[str] = None
    score: float
    matched_by: List[str]
    semantic_rank: Optional[int] = None
    keyword_rank: Optional[int] = None
    source_type: Optional[str] = None
    added_at: Optional[str] = None

class JobItem(BaseModel):
    id: int
    file_path: str
    source_type: Optional[str]
    status: str
    stage: str
    progress: float
    retries: int
    max_retries: int
    error_message: Optional[str]
    created_at: str
    updated_at: str