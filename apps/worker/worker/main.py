import asyncio

import structlog
from arq import cron
from arq.connections import RedisSettings

from worker.config import settings
from worker.tasks.indexowanie import indeksuj_dokument

log = structlog.get_logger()


async def startup(ctx: dict) -> None:
    log.info("worker_startup", redis=settings.redis_url)


async def shutdown(ctx: dict) -> None:
    log.info("worker_shutdown")


async def heartbeat(ctx: dict) -> None:
    log.info("worker_heartbeat")


class WorkerSettings:
    functions = [indeksuj_dokument]
    cron_jobs = [
        cron(heartbeat, minute={0, 15, 30, 45}),
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 10
    job_timeout = 300
    keep_result = 3600


if __name__ == "__main__":
    from arq import run_worker
    run_worker(WorkerSettings)
