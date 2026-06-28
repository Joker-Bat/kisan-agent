# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import contextlib
import os
import time
from collections import defaultdict
from collections.abc import AsyncIterator

import google.auth
from a2a.server.tasks import InMemoryTaskStore
from fastapi import FastAPI, Request, responses
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.runners import Runner
from google.cloud import logging as google_cloud_logging

from app.app_utils import services
from app.app_utils.a2a import attach_a2a_routes
from app.app_utils.reasoning_engine_adapter import attach_reasoning_engine_routes
from app.app_utils.log_config import setup_logging
from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback

setup_telemetry()
setup_logging()
_, project_id = google.auth.default()
logging_client = google_cloud_logging.Client()
logger = logging_client.logger(__name__)
allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Runner for the A2A path, sharing the same session/artifact services as the
    # adk_api and reasoning_engine paths (see services.py). Imported here so the
    # agent is built after env/telemetry setup.
    from app.agent import app as adk_app
    from app.agent import root_agent

    runner = Runner(
        app=adk_app,
        session_service=services.get_session_service(),
        artifact_service=services.get_artifact_service(),
        auto_create_session=True,
    )
    # Shared by the A2A path and the reasoning_engine adapter routes.
    app.state.runner = runner
    app.state.agent_app_name = adk_app.name
    await attach_a2a_routes(
        app,
        agent=root_agent,
        runner=runner,
        task_store=InMemoryTaskStore(),
        rpc_path=f"/a2a/{adk_app.name}",
    )
    yield


app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    artifact_service_uri=services.ARTIFACT_SERVICE_URI,
    allow_origins=allow_origins,
    session_service_uri=services.SESSION_SERVICE_URI,
    otel_to_cloud=True,
    lifespan=lifespan,
)
app.title = "kisan-agent"
app.description = "API for interacting with the Agent kisan-agent"

# Rate limiting defaults (read from env vars on every request for runtime
# configurability — update via `gcloud run services update --update-env-vars`
# without rebuilding the container image).
RATE_LIMIT_REQUESTS_DEFAULT = 10
RATE_LIMIT_WINDOW_DEFAULT = 60

# Simple in-memory sliding window rate limiter
# Structure: client_ip -> list of timestamps of recent requests
request_history: dict[str, list[float]] = defaultdict(list)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Only rate limit API calls to prevent blocking static files or metadata
    if request.url.path.startswith("/api/") or request.url.path.startswith("/a2a/"):
        # Read limits on every request so env var changes take effect immediately
        max_requests = int(
            os.getenv("RATE_LIMIT_REQUESTS", str(RATE_LIMIT_REQUESTS_DEFAULT))
        )
        window_seconds = int(
            os.getenv("RATE_LIMIT_WINDOW", str(RATE_LIMIT_WINDOW_DEFAULT))
        )

        # Get client IP (resolving proxy header for Cloud Run)
        client_ip = request.headers.get("x-forwarded-for")
        if client_ip:
            # Take the first IP if multiple are passed in the chain
            client_ip = client_ip.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        now = time.time()
        # Filter out timestamps older than the rate limit window
        request_history[client_ip] = [
            t for t in request_history[client_ip] if now - t < window_seconds
        ]

        if len(request_history[client_ip]) >= max_requests:
            return responses.JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "requests_limit": max_requests,
                    "window_seconds": window_seconds,
                },
            )

        # Record this request
        request_history[client_ip].append(now)

    response = await call_next(request)
    return response


# Proxy routes so the Vertex AI Console Playground (reasoning_engine SDK) can
# talk to this agent alongside the native adk_api routes.
attach_reasoning_engine_routes(app)


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    logger.log_struct(feedback.model_dump(), severity="INFO")
    return {"status": "success"}


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
