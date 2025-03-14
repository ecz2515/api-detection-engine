from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ApiRequest(BaseModel):
    """Model representing an API request from HAR data."""

    url: str
    method: str
    query_params: Dict[str, str] = Field(default_factory=dict)
    headers: Dict[str, str] = Field(default_factory=dict)
    post_data: Optional[str] = None


class FilteredEndpoint(BaseModel):
    """Model representing a filtered endpoint for LLM analysis."""

    url: str
    methods: List[str]
    params: Dict[str, Any] = Field(default_factory=dict)
    sample_headers: Dict[str, str] = Field(default_factory=dict)
    sample_post_data: Optional[str] = None


class EndpointAnalysis(BaseModel):
    """Model representing an analyzed endpoint."""

    url: str
    explanation: str
    usefulness_score: int = Field(..., ge=0, le=100)


class MatchedRequest(BaseModel):
    """Model representing a matched HAR request with a valuable endpoint."""

    url: str
    method: str
    headers: Dict[str, str]
    status_code: int


class HeadersRequest(BaseModel):
    """Model representing a request for header optimization."""

    api_endpoint: str
    method: str
    necessary_headers: Dict[str, str]


class HeadersResponse(BaseModel):
    """Model representing the response from header optimization."""

    requests: List[HeadersRequest]


class EndpointDocumentation(BaseModel):
    """Model representing the final documented endpoint."""

    url: str
    description: str
    usefulness_score: int
    method: str
    required_headers: Dict[str, str]
    example_params: Dict[str, Any] = Field(default_factory=dict)
    curl_example: str
    notes: Optional[str] = None


class ApiDetectionResults(BaseModel):
    """Model representing the complete results of the API detection process."""

    endpoints: List[EndpointDocumentation]
