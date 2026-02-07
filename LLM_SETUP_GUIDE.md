# LLM Setup Guide - Flash Service

This guide explains how to connect Flash to different LLM providers.

## 🎯 Supported Providers

- **Azure OpenAI** - Enterprise-grade OpenAI models on Azure
- **OpenAI** - Direct OpenAI API access
- **Google Gemini** - Google's latest AI models
- **Ollama** - Run open-source models locally (free, private)

---

## 📦 Installation

### Base Requirements
```bash
pip install openai>=1.10.0
```

### Provider-Specific
```bash
# For Gemini
pip install google-generativeai

# For Ollama (httpx already in requirements)
# Just install Ollama desktop app
```

---

## ⚙️ Configuration

### 1. Copy Environment Template
```bash
cp .env.example .env
```

### 2. Choose Your Provider

Edit `.env` and set:
```bash
FLASH_LLM_PROVIDER=<your_choice>
```

Options: `azure_openai`, `openai`, `gemini`, `ollama`

---

## 🔧 Setup Instructions by Provider

### Option 1: Azure OpenAI (Recommended for Production)

**Pros:** Enterprise SLA, data privacy, compliance  
**Cons:** Requires Azure account

**Setup:**
1. Create an Azure OpenAI resource: https://portal.azure.com
2. Deploy a model (e.g., `gpt-4`)
3. Get endpoint and API key
4. Configure `.env`:
```bash
FLASH_LLM_PROVIDER=azure_openai
FLASH_AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
FLASH_AZURE_OPENAI_API_KEY=abc123...
FLASH_AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
```

---

### Option 2: OpenAI (Easiest)

**Pros:** Fastest setup, latest models  
**Cons:** Usage-based pricing, data leaves your infrastructure

**Setup:**
1. Sign up at https://platform.openai.com
2. Create API key: https://platform.openai.com/api-keys
3. Configure `.env`:
```bash
FLASH_LLM_PROVIDER=openai
FLASH_OPENAI_API_KEY=sk-proj-abc123...
FLASH_OPENAI_MODEL=gpt-4-turbo-preview
```

**Model Options:**
- `gpt-4-turbo-preview` - Most capable
- `gpt-4` - Stable version
- `gpt-3.5-turbo` - Faster, cheaper

---

### Option 3: Google Gemini

**Pros:** Free tier available, competitive pricing  
**Cons:** Different API style, may need adjustments

**Setup:**
1. Get API key: https://makersuite.google.com/app/apikey
2. Install SDK: `pip install google-generativeai`
3. Configure `.env`:
```bash
FLASH_LLM_PROVIDER=gemini
FLASH_GEMINI_API_KEY=AIza...
FLASH_GEMINI_MODEL=gemini-pro
```

---

### Option 4: Ollama (Local - FREE!)

**Pros:** 100% free, private, no API keys needed  
**Cons:** Requires local GPU, slower inference

**Setup:**
1. Install Ollama: https://ollama.ai
2. Pull a model:
```bash
ollama pull llama2        # 7B model - good balance
ollama pull mistral       # Alternative
ollama pull llama2:70b    # More capable, needs 40GB+ RAM
```
3. Start Ollama (usually runs automatically)
4. Configure `.env`:
```bash
FLASH_LLM_PROVIDER=ollama
FLASH_OLLAMA_BASE_URL=http://localhost:11434
FLASH_OLLAMA_MODEL=llama2
```

**Available Models:**
- `llama2` - Default, good for most tasks
- `mistral` - Faster, smaller
- `codellama` - Optimized for code
- `llama2:70b` - Most capable (requires 40GB+ RAM)

---

## 🚀 Testing Your Setup

### 1. Start the server
```bash
uvicorn app.main:app --reload
```

### 2. Test the health endpoint
```bash
curl http://localhost:8000/api/flash/health
```

### 3. Test job analysis (uses LLM)
```bash
curl -X POST http://localhost:8000/api/flash/analyze-job \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Looking for a Senior Python Engineer with FastAPI experience..."
  }'
```

If configured correctly, you'll get a detailed job analysis response.

---

## 🔄 Switching Providers

Simply change the `FLASH_LLM_PROVIDER` variable and restart:

```bash
# In .env
FLASH_LLM_PROVIDER=openai  # Change to desired provider
```

Restart server:
```bash
# Ctrl+C to stop
uvicorn app.main:app --reload
```

---

## 🐛 Troubleshooting

### Error: "LLM is disabled in settings"
- Set `FLASH_ENABLE_LLM=true` in `.env`

### Error: "Azure OpenAI credentials not configured"
- Check that endpoint and API key are set correctly
- Verify no extra spaces in `.env` file

### Error: "Failed to initialize LLM client"
- Check logs for specific error
- Verify API keys are valid
- For Ollama: ensure service is running (`ollama serve`)

### Ollama: "Connection refused"
- Start Ollama: `ollama serve`
- Check if running: `curl http://localhost:11434/api/tags`

---

## 💰 Cost Comparison

| Provider | Free Tier | Cost (per 1M tokens) | Notes |
|----------|-----------|----------------------|-------|
| **Ollama** | ✅ Unlimited | FREE | Requires local hardware |
| **Gemini** | ✅ 60 req/min | ~$0.50-1.50 | Good free tier |
| **OpenAI** | ❌ | $30 (GPT-4) | Pay-as-you-go |
| **Azure OpenAI** | ❌ | $30 (GPT-4) | Enterprise pricing |

---

## 🔐 Security Best Practices

1. **Never commit `.env` to git**
   ```bash
   # Already in .gitignore
   echo ".env" >> .gitignore
   ```

2. **Use environment variables in production**
   - Don't hardcode API keys
   - Use Azure Key Vault or similar

3. **Rotate keys regularly**
   - Change API keys every 90 days

4. **Monitor usage**
   - Set up billing alerts
   - Track API usage

---

## 📚 Advanced: Custom Provider

Want to add another LLM provider? Edit `llm_client.py`:

```python
class CustomLLMClient(BaseLLMClient):
    def __init__(self):
        # Your initialization
        pass
    
    async def chat_completion(self, messages, temperature, max_tokens, **kwargs):
        # Your implementation
        pass
    
    async def close(self):
        pass
```

Then add to factory:
```python
def get_llm_client(provider: Optional[str] = None):
    # ... existing code ...
    elif provider == "custom":
        return CustomLLMClient()
```

---

## 📞 Support

For issues:
1. Check logs: The server will print detailed error messages
2. Verify `.env` configuration
3. Test API keys with provider's playground first
4. Open an issue in the repo with logs

---

## ✅ Quick Start Checklist

- [ ] Chose LLM provider
- [ ] Copied `.env.example` to `.env`
- [ ] Added API keys/credentials
- [ ] Set `FLASH_LLM_PROVIDER` correctly
- [ ] Installed provider-specific packages (if needed)
- [ ] Started server
- [ ] Tested `/health` endpoint
- [ ] Tested `/analyze-job` endpoint
- [ ] 🎉 Ready to use!
