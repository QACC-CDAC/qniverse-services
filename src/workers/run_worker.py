import asyncio
from src.services.cache_service import cache_service
from src.workers.package_worker import worker_loop

async def main():
    print("🚀 Starting package worker...")

    await cache_service.initialize()

    if not cache_service.client:
        raise RuntimeError("Redis not initialized")

    print("✅ Worker connected to Redis")

    await worker_loop()

if __name__ == "__main__":
    asyncio.run(main())