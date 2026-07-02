"""Sends a payload to the Teams Workflows webhook.

A successful Workflows webhook returns HTTP 202 with an empty body, so we
treat any 2xx as success and surface the run-history-style error otherwise.
"""

import requests

from . import config


def send(payload: dict) -> None:
    resp = requests.post(
        config.TEAMS_WEBHOOK_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    if not (200 <= resp.status_code < 300):
        raise RuntimeError(
            f"Teams webhook returned {resp.status_code}: {resp.text[:500]}"
        )
