"""Custom Airflow operator for the HERE Traffic Flow API."""

from __future__ import annotations

import json
import logging
from typing import Any

import requests
from airflow.models import BaseOperator

logger = logging.getLogger(__name__)

HERE_FLOW_API_URL = "https://data.traffic.hereapi.com/v7/flow"


class HereTrafficExtractOperator(BaseOperator):
    """Fetch traffic flow data from the HERE API and return the JSON payload.

    The operator builds a circle-based query around a centre coordinate and
    fetches shape-level traffic flow information.  The raw JSON response is
    serialised to a string so it can be passed via XCom.

    Parameters
    ----------
    api_key : str
        HERE API key (prefer pulling from ``Variable`` or a Secrets backend).
    center_lat : float
        Latitude of the query circle centre.
    center_lng : float
        Longitude of the query circle centre.
    radius_m : int
        Radius in metres for the circle query (default 20 000 m).
    """

    template_fields = ("api_key",)

    def __init__(
        self,
        *,
        api_key: str,
        center_lat: float = 10.777195,
        center_lng: float = 106.695364,
        radius_m: int = 20_000,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.api_key = api_key
        self.center_lat = center_lat
        self.center_lng = center_lng
        self.radius_m = radius_m

    def execute(self, context: Any) -> str:
        params = {
            "apiKey": self.api_key,
            "in": f"circle:{self.center_lat},{self.center_lng};r={self.radius_m}",
            "locationReferencing": "shape",
        }

        logger.info("HERE API request — centre=(%s, %s), radius=%sm",
                     self.center_lat, self.center_lng, self.radius_m)

        response = requests.get(HERE_FLOW_API_URL, params=params, timeout=30)
        response.raise_for_status()

        payload = response.json()
        results_count = len(payload.get("results", []))
        logger.info("Received %d flow results from HERE API", results_count)

        return json.dumps(payload)
