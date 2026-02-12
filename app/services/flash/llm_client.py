"""
LLM Client Factory - Supports multiple providers
Supports: Azure OpenAI, OpenAI, Google Gemini, Local Models (Ollama)
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Union
from enum import Enum
import logging

from app.services.flash.config import settings

logger = logging.getLogger(__name__)

# Type alias for messages
MessageDict = Dict[str, str]


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    AZURE_OPENAI = "azure_openai"
    OPENAI = "openai"
    GEMINI = "gemini"
    OLLAMA = "ollama"  # Local models


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ) -> str:
        """
        Generate chat completion
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        pass
    
    @abstractmethod
    async def close(self):
        """Clean up resources"""
        pass


class AzureOpenAIClient(BaseLLMClient):
    """Azure OpenAI implementation"""
    
    def __init__(self):
        from openai import AsyncAzureOpenAI
        
        if not settings.azure_openai_endpoint or not settings.azure_openai_api_key:
            raise ValueError("Azure OpenAI credentials not configured")
        
        self.client = AsyncAzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version
        )
        self.deployment_name = settings.azure_openai_deployment_name
        logger.info(f"Initialized Azure OpenAI client with deployment: {self.deployment_name}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ) -> str:
        try:
            # Type cast for OpenAI API - messages are compatible
            response = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,  # type: ignore
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Azure OpenAI API call failed: {e}")
            raise
    
    async def close(self):
        await self.client.close()


class OpenAIClient(BaseLLMClient):
    """OpenAI (standard) implementation"""
    
    def __init__(self):
        from openai import AsyncOpenAI
        
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model  # e.g., "gpt-4", "gpt-3.5-turbo"
        logger.info(f"Initialized OpenAI client with model: {self.model}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ) -> str:
        try:
            # Type cast for OpenAI API - messages are compatible
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    async def close(self):
        await self.client.close()


class GeminiClient(BaseLLMClient):
    """Google Gemini implementation"""
    
    def __init__(self):
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError:
            raise ImportError("Install google-generativeai: pip install google-generativeai")
        
        if not settings.gemini_api_key:
            raise ValueError("Gemini API key not configured")
        
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)  # e.g., "gemini-pro"
        logger.info(f"Initialized Gemini client with model: {settings.gemini_model}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ) -> str:
        try:
            # Convert OpenAI-style messages to Gemini format
            prompt = self._convert_messages(messages)
            
            # Gemini uses different parameter names
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            
            response = await self.model.generate_content_async(
                prompt,
                generation_config=generation_config
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI message format to Gemini prompt"""
        # Simple conversion - combine all messages
        parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                parts.append(f"Instructions: {content}")
            elif role == "user":
                parts.append(content)
            elif role == "assistant":
                parts.append(f"Previous response: {content}")
        return "\n\n".join(parts)
    
    async def close(self):
        pass  # Gemini has no explicit close


class OllamaClient(BaseLLMClient):
    """Ollama (local models) implementation"""
    
    def __init__(self):
        import httpx
        
        self.base_url = settings.ollama_base_url or "http://localhost:11434"
        self.model = settings.ollama_model or "llama2"
        self.client = httpx.AsyncClient(timeout=60.0)
        logger.info(f"Initialized Ollama client with model: {self.model}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ) -> str:
        try:
            # Ollama API format
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            raise
    
    async def close(self):
        await self.client.aclose()


# ===== Factory Function =====

def get_llm_client(provider: Optional[str] = None) -> Optional[BaseLLMClient]:
    """
    Factory function to create LLM client based on configuration
    
    Args:
        provider: Override provider (if None, uses settings.llm_provider)
        
    Returns:
        BaseLLMClient instance or None if disabled
    """
    if not settings.enable_llm:
        logger.warning("LLM is disabled in settings")
        return None
    
    provider = provider or settings.llm_provider
    
    try:
        if provider == LLMProvider.AZURE_OPENAI:
            return AzureOpenAIClient()
        elif provider == LLMProvider.OPENAI:
            return OpenAIClient()
        elif provider == LLMProvider.GEMINI:
            return GeminiClient()
        elif provider == LLMProvider.OLLAMA:
            return OllamaClient()
        else:
            logger.error(f"Unknown LLM provider: {provider}")
            return None
    except Exception as e:
        logger.error(f"Failed to initialize LLM client: {e}")
        return None


# ===== Convenience wrapper for services =====

async def call_llm(
    prompt: str,
    client: Optional[BaseLLMClient] = None,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 500
) -> str:
    """
    Simplified LLM call wrapper
    
    Args:
        prompt: User prompt
        client: LLM client (if None, creates new one)
        system_prompt: Optional system prompt
        temperature: Sampling temperature
        max_tokens: Max tokens to generate
        
    Returns:
        Generated text
    """
    if not client:
        client = get_llm_client()
        if not client:
            return ""
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    try:
        return await client.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return ""