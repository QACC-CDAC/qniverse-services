"""Language information endpoints"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, List

from src.models import Language, LanguageInfo, LanguagesResponse
from src.config import get_settings
from src.utils.logger import logger

router = APIRouter()
settings = get_settings()


@router.get(
    "/",
    response_model=LanguagesResponse,
    summary="Get supported languages",
    description="Get list of all supported programming languages with their capabilities"
)
async def get_supported_languages() -> LanguagesResponse:
    """
    Get detailed information about supported languages
    """
    languages = []
    
    for source_lang, targets in settings.SUPPORTED_LANGUAGES.items():
        language_info = LanguageInfo(
            name=source_lang,
            version="3.11" if source_lang == "python" else "latest",  # Example version
            targets=targets,
            features=get_language_features(source_lang)
        )
        languages.append(language_info)
    
    logger.info(f"Retrieved supported languages: {len(languages)} languages")
    
    return {
        "languages": languages,
        "total_count": len(languages)
    }


@router.get(
    "/{language}/targets",
    response_model=List[str],
    summary="Get target languages",
    description="Get all target languages available for a source language"
)
async def get_target_languages(language: str) -> List[str]:
    """
    Get all target languages for a specific source language
    """
    if language not in settings.SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language '{language}' is not supported"
        )
    
    return settings.SUPPORTED_LANGUAGES[language]


@router.get(
    "/pairs",
    response_model=List[Dict[str, str]],
    summary="Get all language pairs",
    description="Get all supported source-target language pairs"
)
async def get_all_pairs() -> List[Dict[str, str]]:
    """
    Get all supported language pairs
    """
    pairs = []
    
    for source, targets in settings.SUPPORTED_LANGUAGES.items():
        for target in targets:
            pairs.append({
                "source": source,
                "target": target
            })
    
    logger.info(f"Retrieved {len(pairs)} language pairs")
    return pairs


def get_language_features(language: str) -> List[str]:
    """Get features supported for a language"""
    features_map = {
        "python": ["functions", "classes", "async/await", "type hints", "decorators", "generators"],
        "javascript": ["functions", "classes", "async/await", "promises", "closures", "prototypes"],
        "typescript": ["functions", "classes", "interfaces", "generics", "async/await", "decorators"],
        "java": ["classes", "interfaces", "generics", "lambda", "streams", "annotations"],
        "go": ["functions", "structs", "interfaces", "goroutines", "channels", "defer"],
        "rust": ["functions", "structs", "traits", "enums", "pattern matching", "ownership"],
        "csharp": ["classes", "interfaces", "generics", "LINQ", "async/await", "properties"]
    }
    
    return features_map.get(language, ["basic syntax"])