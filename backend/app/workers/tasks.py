import asyncio
import json
import logging
import random
import time
from celery import Task
import httpx

from backend.app.core.security import SecurityEngine, SSRFSecurityException
from backend.app.workers.celery_app import celery_app

logger = logging.getLogger("celery_dispatch_tasks")


class BaseDeliveryTask(Task):
    """Abstract base task providing lifecycle failure hooks for DLQ transition."""
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.critical(
            "[DLQ TRANSITION] Task %s exhausted all retry attempts. Routing to Dead-Letter Queue. Error: %s",
            task_id, exc,
        )


@celery_app.task(
    bind=True,
    base=BaseDeliveryTask,
    name="tasks.dispatch_webhook",
    max_retries=5,
    acks_late=True,
    reject_on_worker_lost=True,
)
def dispatch_webhook_task(
    self,
    event_id: str,
    subscription_id: str,
    target_url: str,
    secret: str,
    payload: dict,
    attempt: int = 1,
):
    """
    Executes resilient outbound HTTP webhook delivery.
    Applies SSRF security checks, HMAC signing, strict timeouts,
    and exponential backoff with full jitter on transient failures.
    """
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode("utf-8")
    timestamp = int(time.time())

    # 1. Socket-Level SSRF Check & DNS Resolution
    try:
        resolved_ip = SecurityEngine.validate_and_resolve_url(target_url)
    except SSRFSecurityException as ssrf_err:
        logger.error("[SECURITY REJECTION] %s. Aborting delivery permanently.", ssrf_err)
        return {"status": "REJECTED_SSRF", "reason": str(ssrf_err)}

    # 2. Cryptographic Signature Generation
    signature = SecurityEngine.generate_hmac_signature(payload_bytes, secret, timestamp)
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Sentinel-Event-Dispatcher/1.0",
        "X-Sentinel-Delivery": self.request.id or "direct",
        "X-Sentinel-Timestamp": str(timestamp),
        "X-Sentinel-Signature": f"t={timestamp},v1={signature}",
    }

    # 3. Synchronous-to-Async HTTP Dispatch with Strict Timeouts
    async def _send_request() -> tuple[int, str]:
        timeout = httpx.Timeout(connect=2.0, read=5.0, write=5.0, pool=10.0)
        async with httpx.AsyncClient(timeout=timeout, verify=True) as client:
            response = await client.post(target_url, content=payload_bytes, headers=headers)
            return response.status_code, response.text

    try:
        status_code, response_body = asyncio.run(_send_request())

        # Success case: 2xx range
        if 200 <= status_code < 300:
            logger.info("Webhook %s delivered successfully to %s (HTTP %d)", event_id, target_url, status_code)
            return {
                "status": "DELIVERED",
                "attempt": attempt,
                "status_code": status_code,
                "delivery_id": self.request.id,
            }

        # Client error (4xx except 429) -> Permanent failure, do not retry
        if 400 <= status_code < 500 and status_code != 429:
            logger.warning("Permanent client error HTTP %d received from %s", status_code, target_url)
            return {
                "status": "CLIENT_ERROR_ABORTED",
                "attempt": attempt,
                "status_code": status_code,
                "response": response_body[:200],
            }

        error_reason = f"HTTP status {status_code}"

    except (httpx.RequestError, httpx.TimeoutException) as req_err:
        error_reason = f"Network or Timeout Error: {type(req_err).__name__}"

    # 4. Exponential Backoff with Full Jitter Computation:
    # Sleep = random(0.5, min(MAX_BACKOFF, BASE * 2 ^ attempt))
    base_backoff = 2.0
    max_backoff = 60.0
    calculated_backoff = min(max_backoff, base_backoff * (2 ** attempt))
    jittered_delay = random.uniform(0.5, calculated_backoff)

    logger.warning(
        "[RETRYING] Delivery failed: %s. Attempt: %d/5. Retrying in %.2fs.",
        error_reason, attempt, jittered_delay,
    )

    try:
        raise self.retry(
            countdown=jittered_delay,
            exc=Exception(error_reason),
            queue="retries",
            kwargs={
                "event_id": event_id,
                "subscription_id": subscription_id,
                "target_url": target_url,
                "secret": secret,
                "payload": payload,
                "attempt": attempt + 1,
            },
        )
    except self.MaxRetriesExceededError:
        logger.error("[DLQ] Max retries exhausted for event %s to %s", event_id, target_url)
        return {
            "status": "DEAD_LETTER",
            "attempt": attempt,
            "error": "Max retries exceeded; routed to DLQ.",
        }
