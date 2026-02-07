"""
Example: Using Flash with Different LLM Providers

This script demonstrates how to test each LLM provider.
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the LLM client
from app.services.flash.llm_client import get_llm_client, BaseLLMClient


async def test_llm(provider_name: str):
    """Test a specific LLM provider"""
    print(f"\n{'='*60}")
    print(f"Testing: {provider_name}")
    print(f"{'='*60}")
    
    # Set provider (override environment)
    os.environ['FLASH_LLM_PROVIDER'] = provider_name
    
    try:
        # Get client
        client = get_llm_client(provider=provider_name)
        
        if not client:
            print(f"❌ Failed to initialize {provider_name} - check credentials")
            return
        
        print(f"✅ Client initialized successfully")
        
        # Test simple prompt
        test_prompt = "List 3 key skills for a Python developer in one sentence."
        
        print(f"\n📤 Sending test prompt...")
        messages = [
            {"role": "user", "content": test_prompt}
        ]
        
        response = await client.chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=100
        )
        
        print(f"\n📥 Response:\n{response}")
        print(f"\n✅ Test completed successfully for {provider_name}!")
        
        # Cleanup
        await client.close()
        
    except Exception as e:
        print(f"\n❌ Error testing {provider_name}: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run tests for all configured providers"""
    print("🚀 Flash LLM Provider Test Suite")
    print("=" * 60)
    
    # Load current settings
    from app.services.flash.config import settings
    
    print(f"\nCurrent Config:")
    print(f"  LLM Enabled: {settings.enable_llm}")
    print(f"  Provider: {settings.llm_provider}")
    
    providers_to_test = []
    
    # Check which providers are configured
    if settings.azure_openai_endpoint and settings.azure_openai_api_key:
        providers_to_test.append('azure_openai')
    
    if settings.openai_api_key:
        providers_to_test.append('openai')
    
    if settings.gemini_api_key:
        providers_to_test.append('gemini')
    
    # Ollama is always available if running
    providers_to_test.append('ollama')
    
    if not providers_to_test:
        print("\n⚠️  No providers configured! Please set API keys in .env")
        return
    
    print(f"\n📋 Testing {len(providers_to_test)} provider(s): {', '.join(providers_to_test)}")
    
    # Test each provider
    for provider in providers_to_test:
        await test_llm(provider)
        await asyncio.sleep(1)  # Brief pause between tests
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)


# === Convenience Functions ===

async def quick_test_azure():
    """Quick test for Azure OpenAI only"""
    await test_llm('azure_openai')


async def quick_test_openai():
    """Quick test for OpenAI only"""
    await test_llm('openai')


async def quick_test_gemini():
    """Quick test for Gemini only"""
    await test_llm('gemini')


async def quick_test_ollama():
    """Quick test for Ollama only"""
    await test_llm('ollama')


# === Usage Examples ===

async def example_job_analysis():
    """Example: Analyze a job description"""
    print("\n" + "="*60)
    print("Example: Job Description Analysis")
    print("="*60)
    
    from app.services.flash.services.job_analyzer import JobAnalyzerService
    
    client = get_llm_client()
    if not client:
        print("❌ No LLM client available")
        return
    
    analyzer = JobAnalyzerService(llm_client=client)
    
    job_desc = """
    Senior Python Developer
    
    We're looking for an experienced Python developer with:
    - 5+ years Python experience
    - FastAPI or Django expertise
    - AWS/Azure cloud experience
    - Docker & Kubernetes
    - Strong communication skills
    """
    
    print(f"\n📄 Job Description:\n{job_desc}")
    print(f"\n🔍 Analyzing...")
    
    result = await analyzer.analyze_job(job_desc)
    
    print(f"\n📊 Analysis Results:")
    print(f"  Required Skills: {result.required_skills}")
    print(f"  Technologies: {result.technologies}")
    print(f"  Seniority: {result.seniority_level}")
    
    await client.close()


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║           Flash LLM Provider Testing Tool                 ║
║                                                            ║
║  This script tests your LLM configuration and connection  ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # Run main test suite
    asyncio.run(main())
    
    # Uncomment to run specific tests:
    # asyncio.run(quick_test_openai())
    # asyncio.run(quick_test_ollama())
    # asyncio.run(example_job_analysis())
