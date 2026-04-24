"""Package installation endpoints"""

from fastapi import APIRouter, Depends, Request, HTTPException, status, BackgroundTasks
from typing import List

from src.models import JobStatusResponse, PackageInstallRequest, PackageInstallResponse, PackageInstallResponse, PackageListResponse
from src.services.package_service import package_service
from src.api.dependencies.auth import verify_api_key
from src.middleware.rate_limit import limiter
from src.utils.logger import logger
from src.config import get_settings

router = APIRouter()
settings = get_settings()

# API Endpoints
@router.post(
    "/install",
    response_model=PackageInstallResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Install packages for a user",
    description="""
    Install Python packages in a user's isolated virtual environment.
    
    - Creates a virtual environment for the user if it doesn't exist
    - Installs packages in the background
    - Returns a job ID to track installation progress
    """
)
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_PERIOD}second")
async def install_packages(
    request: Request,
    install_request: PackageInstallRequest,
    api_key: str = Depends(verify_api_key)
) -> PackageInstallResponse:
    """
    Install packages for a user
    """
    request_id = getattr(request.state, "request_id", None)
    
    try:
        result = await package_service.install_packages(
            username=install_request.username,
            packages=install_request.packages
        )
        
        logger.info(
            f"Package installation job created",
            extra={
                "request_id": request_id,
                "job_id": result["job_id"],
                "username": install_request.username,
                "packages": install_request.packages
            }
        )
        
        return PackageInstallResponse(
            job_id=result["job_id"],
            status=result["status"],
            username=result["username"],
            packages=result["packages"],
            created_at=result["created_at"],
            message="Installation started successfully"
        )
        
    except Exception as e:
        logger.error(f"Package installation error: {str(e)}", extra={"request_id": request_id})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/status/{job_id}",
    response_model=JobStatusResponse,
    summary="Get package installation status",
    description="Get the status of a package installation job"
)
async def get_installation_status(
    request: Request,
    job_id: str,
    api_key: str = Depends(verify_api_key)
) -> JobStatusResponse:
    """
    Get status of a package installation job
    """
    request_id = getattr(request.state, "request_id", None)
    
    job_status = package_service.get_job_status(job_id)
    
    if not job_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    logger.debug(f"Job status retrieved", extra={"request_id": request_id, "job_id": job_id})
    
    return JobStatusResponse(**job_status)


@router.get(
    "/user/{username}/jobs",
    response_model=List[JobStatusResponse],
    summary="List user's installation jobs",
    description="List all package installation jobs for a specific user"
)
async def list_user_jobs(
    request: Request,
    username: str,
    limit: int = 10,
    api_key: str = Depends(verify_api_key)
) -> List[JobStatusResponse]:
    """
    List all jobs for a specific user
    """
    request_id = getattr(request.state, "request_id", None)
    
    # Validate username
    if ".." in username or "/" in username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username"
        )
    
    jobs = package_service.list_user_jobs(username, min(limit, 50))
    
    logger.info(f"Listed {len(jobs)} jobs for user {username}", extra={"request_id": request_id})
    
    return [JobStatusResponse(**job) for job in jobs]


@router.get(
    "/user/{username}/packages",
    response_model=PackageListResponse,
    summary="List installed packages",
    description="List all installed packages for a user"
)
async def list_installed_packages(
    request: Request,
    username: str,
    api_key: str = Depends(verify_api_key)
) -> PackageListResponse:
    """
    List all packages installed in user's virtual environment
    """
    request_id = getattr(request.state, "request_id", None)
    
    # Validate username
    if ".." in username or "/" in username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username"
        )
    
    # Get user directory
    from src.services.package_service import package_service as ps
    user_dir = ps._get_user_dir(username)
    
    if not os.path.exists(user_dir):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No virtual environment found for user {username}"
        )
    
    # List installed packages
    try:
        import subprocess
        pip_path = os.path.join(user_dir, "bin", "pip")
        
        if not os.path.exists(pip_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="pip not found in virtual environment"
            )
        
        result = subprocess.run(
            [pip_path, "list", "--format=json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            import json
            packages = json.loads(result.stdout)
        else:
            packages = []
        
        logger.info(f"Listed packages for user {username}", extra={"request_id": request_id})
        
        return PackageListResponse(
            username=username,
            packages=packages,
            environment_path=user_dir
        )
        
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Package listing timed out"
        )
    except Exception as e:
        logger.error(f"Error listing packages: {str(e)}", extra={"request_id": request_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list packages"
        )


@router.delete(
    "/user/{username}/packages/{package_name}",
    summary="Uninstall a package",
    description="Uninstall a specific package from user's virtual environment"
)
async def uninstall_package(
    request: Request,
    username: str,
    package_name: str,
    api_key: str = Depends(verify_api_key)
) -> dict:
    """
    Uninstall a package from user's virtual environment
    """
    request_id = getattr(request.state, "request_id", None)
    
    # Validate inputs
    if ".." in username or "/" in username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username"
        )
    
    # Get user directory
    from src.services.package_service import package_service as ps
    user_dir = ps._get_user_dir(username)
    
    if not os.path.exists(user_dir):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No virtual environment found for user {username}"
        )
    
    try:
        import subprocess
        pip_path = os.path.join(user_dir, "bin", "pip")
        
        result = subprocess.run(
            [pip_path, "uninstall", "-y", package_name],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info(f"Uninstalled package {package_name} for user {username}", 
                       extra={"request_id": request_id})
            return {
                "message": f"Successfully uninstalled {package_name}",
                "username": username,
                "package": package_name
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to uninstall {package_name}: {result.stderr}"
            )
            
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Package uninstallation timed out"
        )
    except Exception as e:
        logger.error(f"Error uninstalling package: {str(e)}", extra={"request_id": request_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to uninstall package"
        )


# Import os for file operations
import os