from celery import Celery
from kombu import Exchange, Queue
from backend.app.core.config import settings

celery_app = Celery(
    "sentinel_workers",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.REDIS_URL,
)

# Enterprise Celery Configurations
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Worker Starvation & Fair Scheduling Defenses:
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    # Queues:
    task_queues=[
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("retries", Exchange("retries"), routing_key="retries"),
        Queue("dlq", Exchange("dlq"), routing_key="dlq"),
    ],
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
)

celery_app.autodiscover_tasks(["backend.app.workers"])
