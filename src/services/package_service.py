"""Package installation service for managing Python packages in user virtual environments"""

import os
import subprocess
import threading
import uuid
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from src.utils.logger import logger
from src.config import get_settings
from src.core.exceptions import ValidationError, PackageInstallationError

settings = get_settings()


class PackageInstallationService:
    """Service for managing package installations in isolated virtual environments"""
    
    def __init__(self):
        self.base_dir = settings.PACKAGE_BASE_DIR or "/home/qacc/qns-custom-packages"
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self._ensure_base_directory()
    
    def _ensure_base_directory(self):
        """Ensure the base directory exists"""
        try:
            os.makedirs(self.base_dir, exist_ok=True)
            logger.info(f"Package base directory ensured: {self.base_dir}")
        except Exception as e:
            logger.error(f"Failed to create base directory: {str(e)}")
            raise
    
    def _validate_username(self, username: str) -> bool:
        """Validate username to prevent path traversal"""
        if not username:
            return False
        # Prevent path traversal attacks
        if ".." in username or "/" in username or "\\" in username:
            return False
        # Allow only alphanumeric and underscore
        if not username.replace("_", "").replace("-", "").isalnum():
            return False
        return True
    
    def _get_user_dir(self, username: str) -> str:
        """Get user's virtual environment directory"""
        return os.path.join(self.base_dir, username)
    
    def _create_virtual_env(self, user_dir: str) -> bool:
        """Create a virtual environment for the user"""
        try:
            # Check if venv already exists
            if os.path.exists(os.path.join(user_dir, "bin", "python")):
                logger.info(f"Virtual environment already exists at {user_dir}")
                return True
            
            # Create directory if it doesn't exist
            os.makedirs(user_dir, exist_ok=True)
            
            # Create virtual environment
            cmd = ["python3", "-m", "venv", user_dir]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"Virtual environment created at {user_dir}")
                return True
            else:
                logger.error(f"Failed to create venv: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Virtual environment creation timed out")
            return False
        except Exception as e:
            logger.error(f"Error creating virtual environment: {str(e)}")
            return False
    
    def _install_packages_worker(self, job_id: str, user_dir: str, packages: List[str]):
        """Background worker for package installation"""
        self.jobs[job_id]["status"] = "running"
        self.jobs[job_id]["start_time"] = time.time()
        
        try:
            pip_path = os.path.join(user_dir, "bin", "pip")
            
            # Verify pip exists
            if not os.path.exists(pip_path):
                raise PackageInstallationError(f"pip not found in {user_dir}")
            
            # Install packages
            cmd = [pip_path, "install"] + packages
            
            logger.info(f"Installing packages for job {job_id}: {packages}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(timeout=settings.PACKAGE_INSTALL_TIMEOUT)
            
            self.jobs[job_id]["end_time"] = time.time()
            
            if process.returncode == 0:
                self.jobs[job_id]["status"] = "completed"
                self.jobs[job_id]["output"] = stdout
                logger.info(f"Successfully installed packages for job {job_id}")
            else:
                self.jobs[job_id]["status"] = "failed"
                self.jobs[job_id]["error"] = stderr
                logger.error(f"Failed to install packages for job {job_id}: {stderr}")
                
        except subprocess.TimeoutExpired:
            self.jobs[job_id]["status"] = "failed"
            self.jobs[job_id]["error"] = f"Installation timeout after {settings.PACKAGE_INSTALL_TIMEOUT} seconds"
            self.jobs[job_id]["end_time"] = time.time()
            logger.error(f"Package installation timeout for job {job_id}")
            
        except Exception as e:
            self.jobs[job_id]["status"] = "failed"
            self.jobs[job_id]["error"] = str(e)
            self.jobs[job_id]["end_time"] = time.time()
            logger.error(f"Error installing packages for job {job_id}: {str(e)}")
    
    async def install_packages(
        self, 
        username: str, 
        packages: List[str],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Install packages for a user in their virtual environment"""
        
        # Validate inputs
        if not self._validate_username(username):
            raise ValidationError("Invalid username. Use only alphanumeric characters, underscore, and hyphen.")
        
        if not packages or not isinstance(packages, list):
            raise ValidationError("Packages must be a non-empty list")
        
        # Limit number of packages
        if len(packages) > settings.MAX_PACKAGES_PER_REQUEST:
            raise ValidationError(f"Maximum {settings.MAX_PACKAGES_PER_REQUEST} packages per request")
        
        # Sanitize package names
        sanitized_packages = []
        for package in packages:
            # Basic validation - prevent command injection
            if not package or any(char in package for char in [';', '|', '&', '$', '`', '>', '<']):
                raise ValidationError(f"Invalid package name: {package}")
            sanitized_packages.append(package.strip())
        
        # Get user directory
        user_dir = self._get_user_dir(username)
        
        # Create virtual environment if needed
        if not self._create_virtual_env(user_dir):
            raise PackageInstallationError("Failed to create or access virtual environment")
        
        # Create job
        job_id = str(uuid.uuid4())
        
        self.jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "username": username,
            "packages": sanitized_packages,
            "created_at": time.time(),
            "created_at_iso": datetime.utcnow().isoformat(),
            "start_time": None,
            "end_time": None,
            "output": None,
            "error": None,
            "options": options or {}
        }
        
        # Start background thread
        thread = threading.Thread(
            target=self._install_packages_worker,
            args=(job_id, user_dir, sanitized_packages)
        )
        thread.daemon = True
        thread.start()
        
        logger.info(f"Created package installation job {job_id} for user {username}")
        
        return {
            "job_id": job_id,
            "status": "queued",
            "username": username,
            "packages": sanitized_packages,
            "created_at": self.jobs[job_id]["created_at_iso"]
        }
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a package installation job"""
        job = self.jobs.get(job_id)
        
        if not job:
            return None
        
        # Format response
        return {
            "job_id": job["job_id"],
            "status": job["status"],
            "username": job["username"],
            "packages": job["packages"],
            "created_at": job.get("created_at_iso"),
            "start_time": datetime.utcfromtimestamp(job["start_time"]).isoformat() if job.get("start_time") else None,
            "end_time": datetime.utcfromtimestamp(job["end_time"]).isoformat() if job.get("end_time") else None,
            "duration_seconds": (job["end_time"] - job["start_time"]) if job.get("start_time") and job.get("end_time") else None,
            "output": job.get("output"),
            "error": job.get("error"),
        }
    
    def list_user_jobs(self, username: str, limit: int = 10) -> List[Dict[str, Any]]:
        """List all jobs for a specific user"""
        user_jobs = [
            self.get_job_status(job_id)
            for job_id, job in self.jobs.items()
            if job.get("username") == username
        ]
        
        # Sort by creation time (newest first) and limit
        user_jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return user_jobs[:limit]
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old jobs to prevent memory bloat"""
        current_time = time.time()
        jobs_to_remove = []
        
        for job_id, job in self.jobs.items():
            created_at = job.get("created_at", 0)
            age_hours = (current_time - created_at) / 3600
            
            if age_hours > max_age_hours:
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
        
        if jobs_to_remove:
            logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
        
        return len(jobs_to_remove)


# Singleton instance
package_service = PackageInstallationService()