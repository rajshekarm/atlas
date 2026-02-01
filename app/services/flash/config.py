"""
Configuration management for Flash service
"""
from pydantic import BaseSettings
from typing import Optional


class FlashSettings(BaseSettings):
    """Flash service configuration"""
    
    # Azure OpenAI
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_deployment_name: str = "gpt-4"
    azure_openai_api_version: str = "2024-02-01"
    
    # Azure AI Search
    azure_search_endpoint: Optional[str] = None
    azure_search_api_key: Optional[str] = None
    azure_search_index_name: str = "flash-knowledge-base"
    
    # Azure Blob Storage
    azure_storage_connection_string: Optional[str] = None
    azure_storage_container_name: str = "resumes"
    
    # Local Storage
    local_storage_path: str = "./data/flash"
    resume_storage_path: str = "./data/resumes"
    knowledge_base_path: str = "./data/knowledge_base"
    
    # Service Settings
    max_resume_size_mb: int = 5
    max_answer_length_words: int = 200
    confidence_threshold_high: float = 0.8
    confidence_threshold_medium: float = 0.5
    
    # Guardrails
    enable_guardrails: bool = True
    max_resume_rewrite_percentage: int = 40
    
    class Config:
        env_file = ".env"
        env_prefix = "FLASH_"


# Global settings instance
settings = FlashSettings()
