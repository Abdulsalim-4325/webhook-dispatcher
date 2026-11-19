import asyncio
import logging
from typing import Any
from fastapi import FastAPI, Header, HTTPException, Request, Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock_receiver")

app = FastAPI(
    title="Sentinel Mock Receiver",
    description="Configurable mock webhook target to simulate 200 OK, 500 Failure, Timeouts, and Flakiness.",
    version="1.0.0",
)

# In-memory counter for flaky tests
flaky_counter = {"attempts": 0}


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "mock-receiver"}


@app.post("/webhook/success")
async def webhook_success(
    request: Request,
    x_sentinel_signature: str | None = Header(default=None),
    x_sentinel_timestamp: str | None = Header(default=None),
) -> dict[str, Any]:
    body = await request.json()
    logger.info("Received successful webhook: %s | Sig: %s", body, x_sentinel_signature)
    return {
        "status": "received",
        "acknowledged": True,
        "signature_present": bool(x_sentinel_signature),
    }


@app.post("/webhook/fail")
async def webhook_fail(request: Request) -> Response:
    body = await request.body()
    logger.warning("Simulating 500 Internal Server Error for payload size %d bytes", len(body))
    raise HTTPException(status_code=500, detail="Simulated Destination Downtime")


@app.post("/webhook/slow")
async def webhook_slow(request: Request) -> dict[str, str]:
    # Sleep 6 seconds to trigger client-side read timeout (which defaults to 5s)
    await asyncio.sleep(6.0)
    return {"status": "slow_response_completed"}


@app.post("/webhook/flaky")
async def webhook_flaky(request: Request) -> dict[str, Any]:
    flaky_counter["attempts"] += 1
    attempt = flaky_counter["attempts"]
    if attempt % 3 != 0:
        logger.warning("Flaky attempt %d: Simulating temporary 503 Unavailable", attempt)
        raise HTTPException(status_code=503, detail=f"Flaky endpoint failed (attempt {attempt})")
    
    logger.info("Flaky attempt %d: Successfully recovered!", attempt)
    return {"status": "recovered", "attempt": attempt}
