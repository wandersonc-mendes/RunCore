from typing import Any

from pydantic import BaseModel


class AthleteAnalyticsResponse(BaseModel):
    athlete_id: int
    reference_date: str
    activity_count: int
    calculation_context: dict[str, Any]
    weekly: list[dict[str, Any]]
    pace_baselines: list[dict[str, Any]]
    period_comparison: dict[str, Any]
    data_quality: dict[str, Any]
    analysis_availability: dict[str, Any]
