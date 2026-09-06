from typing import Literal
from pydantic import BaseModel, Field


class VLMQueryRequest(BaseModel):
    """Request payload for natural language satellite image question-answering."""
    scene_id: str = Field(..., min_length=1, description="STAC scene ID to query")
    question: str = Field(..., min_length=1, description="Natural language question about the satellite scene")
    include_ndvi_context: bool = Field(
        default=True,
        description="Whether to include biophysical NDVI statistics as grounded context if available",
    )


class VLMEvidenceItem(BaseModel):
    """Grounded visual observation or analytical evidence supporting the VLM answer."""
    feature: str = Field(..., min_length=1, description="Identified visual feature or area of interest")
    observation: str = Field(..., min_length=1, description="Specific observation or evidence seen in the imagery/metadata")
    confidence: Literal["high", "medium", "low"] = Field(
        ...,
        description="Confidence rating for this specific observation",
    )


class VLMProviderStructuredOutput(BaseModel):
    """Internal schema enforced on the Gemini JSON completion."""
    answer: str = Field(..., min_length=1, description="Synthesized answer to the user question")
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence score between 0.0 and 1.0",
    )
    confidence_level: Literal["high", "medium", "low"] = Field(
        ...,
        description="Overall confidence level",
    )
    evidence: list[VLMEvidenceItem] = Field(
        default_factory=list,
        description="List of specific grounded visual observations",
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Noted caveats regarding spatial resolution, cloud cover, or spectral data",
    )


class VLMQueryResponse(BaseModel):
    """Final API response model for multimodal VLM query endpoint."""
    scene_id: str
    question: str
    answer: str
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0",
    )
    confidence_level: Literal["high", "medium", "low"]
    evidence: list[VLMEvidenceItem] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    model_used: str
    latency_ms: int
    timestamp: str
