# src/services/job_service.py

import json
import time
from typing import Optional, Dict, Any
from src.services.cache_service import cache_service


class JobService:

    def _job_key(self, job_id: str) -> str:
        return f"job:{job_id}"

    def _queue_key(self) -> str:
        return "queue:packages"

    async def create_job(self, job_id: str, data: Dict[str, Any]):
        job = {
            "job_id": job_id,
            "status": "queued",
            "created_at": time.time(),
            **data
        }

        await cache_service.client.set(
            self._job_key(job_id),
            json.dumps(job)
        )

        # push to queue (FIFO)
        await cache_service.client.rpush(
            self._queue_key(),
            job_id
        )

    async def get_job(self, job_id: str) -> Optional[Dict]:
        data = await cache_service.client.get(self._job_key(job_id))
        return json.loads(data) if data else None

    async def update_job(self, job_id: str, updates: Dict):
        job = await self.get_job(job_id)
        if not job:
            return

        job.update(updates)

        await cache_service.client.set(
            self._job_key(job_id),
            json.dumps(job)
        )

    async def pop_job(self) -> Optional[str]:
        # worker pulls next job
        return await cache_service.client.lpop(self._queue_key())


job_service = JobService()