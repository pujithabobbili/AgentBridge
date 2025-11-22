from pydantic import BaseModel
from typing import Dict, Any, List, Optional, Literal


class Intent(BaseModel):
    goal: str
    inputs: Dict[str, Any]
    constraints: Optional[Dict[str, Any]] = None
    budget: Optional[Dict[str, float]] = None
    sla: Optional[Dict[str, int]] = None


class Proposal(BaseModel):
    est_cost_usd: float
    est_latency_ms: int
    confidence: float
    plan: List[str]
    needs: Dict[str, Any] = {}


class Task(BaseModel):
    goal: str
    inputs: Dict[str, Any]
    sla_ms: int = 120000


class Result(BaseModel):
    status: Literal["OK", "PARTIAL", "ERROR"]
    data: Dict[str, Any] = {}
    metrics: Dict[str, Any] = {}
    evidence: Dict[str, Any] = {}
    error: Optional[str] = None


