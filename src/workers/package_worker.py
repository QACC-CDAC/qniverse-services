# src/workers/package_worker.py

import asyncio
import subprocess
import os
import time

from src.services.job_service import job_service

BASE_DIR = "/home/qacc/qns-custom-packages"


async def worker_loop():
    while True:
        job_id = await job_service.pop_job()

        if not job_id:
            await asyncio.sleep(1)
            continue

        job = await job_service.get_job(job_id)
        if not job:
            continue

        await job_service.update_job(job_id, {
            "status": "running",
            "start_time": time.time()
        })

        try:
            # user_dir = os.path.join(BASE_DIR, job["username"])

            # if not os.path.exists(user_dir):
            #     os.makedirs(user_dir)
            #     subprocess.run(["python3", "-m", "venv", user_dir])

            # pip_path = os.path.join(user_dir, "bin", "pip")

            # if job["action"] == "install":
            #     cmd = [pip_path, "install"] + job["packages"]
            # else:
            #     cmd = [pip_path, "uninstall", "-y"] + job["packages"]
            
            
            if job["action"] == "install":
                cmd = ["ls -la"]
            else:
                cmd = ["whoami"]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                await job_service.update_job(job_id, {
                    "status": "completed",
                    "output": result.stdout,
                    "end_time": time.time()
                })
            else:
                await job_service.update_job(job_id, {
                    "status": "failed",
                    "error": result.stderr,
                    "end_time": time.time()
                })

        except Exception as e:
            await job_service.update_job(job_id, {
                "status": "failed",
                "error": str(e),
                "end_time": time.time()
            })