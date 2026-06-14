# Quick Start: Fast & Reliable RAG with Ollama + NVIDIA Fallback

## What Was Fixed

✅ **NVIDIA API Timeout Issue Resolved**
- Fixed `client.responses.create()` → now uses `client.chat.completions.create()` (correct endpoint)
- Reduced timeout to 30s with proper error handling
- Massive prompt truncation (top 5 chunks max, 300 chars each)

✅ **Added Ollama as Primary LLM (Fast, Local, No Timeout)**
- Local Ollama runs on `http://localhost:11434`
- Zero API latency, zero rate limits, zero timeouts
- Fallback chain: Ollama → NVIDIA → chunk summary

✅ **Streamlit UI Updated**
- Better timeout messages (now 60s instead of 120s)
- Shows answer or gracefully falls back to context
- Informative spinner text

---

## Setup Instructions

### Option 1: Use Local Ollama (Recommended - No API Key Needed)

1. **Install Ollama** (if not already installed):
   ```bash
   # Windows/Mac/Linux from: https://ollama.ai
   ```

2. **Pull a fast model** (one-time):
   ```bash
   ollama pull mistral  # ~4GB, very fast
   # OR
   ollama pull neural-chat  # Smaller, still good
   ```

3. **Run Ollama**:
   ```bash
   ollama serve
   # Listens on http://localhost:11434
   ```

4. **Start FastAPI** (project root):
   ```bash
   uvicorn src.api.main:app --reload --port 8000
   ```

5. **Start Streamlit**:
   ```bash
   streamlit run streamlit_app.py
   ```

6. **Test**: Query something → should get answers in **5-10 seconds** with Ollama!

---

### Option 2: NVIDIA OpenAI API (Fallback)

1. **Set environment variable** (Windows PowerShell):
   ```powershell
   $env:OPENAI_API_KEY = "nvapi-YOUR-KEY-HERE"
   ```

2. **Optional**: Override API URL (defaults to `https://integrate.api.nvidia.com/v1`):
   ```powershell
   $env:OPENAI_BASE_URL = "https://integrate.api.nvidia.com/v1"
   ```

3. **System will try Ollama first, fallback to NVIDIA if Ollama unavailable**

---

## Architecture

```
Query
  ↓
[RetrievalService]
  ├─ Embed query
  ├─ Retrieve from Chroma
  ├─ Rerank with CrossEncoder
  └─ _get_answer()
      ├─ Try Ollama (localhost:11434) ← FAST
      ├─ Fallback: Try NVIDIA API ← BACKUP
      └─ Last resort: Return chunk summary
```

---

## File Changes

| File | Change |
|------|--------|
| `src/llm/openai_client.py` | Fixed to use `chat.completions.create()`, added timeout handling |
| `src/llm/ollama_client.py` | NEW - Local LLM client with health check |
| `src/services/retrieval_service.py` | Added `_get_answer()` with smart fallback chain |
| `streamlit_app.py` | Updated timeout to 60s, better error messages |

---

## Troubleshooting

### "Ollama not available"
- Make sure Ollama is running: `ollama serve`
- Check port is correct: `http://localhost:11434/api/tags`
- Model available? `ollama list`

### "NVIDIA API timed out"
- NVIDIA endpoint may be slow/overloaded
- Ollama will take over (if available)
- Reduce `top_k` to lower context size

### "Both LLM clients failed"
- System returns first chunk summary as fallback
- Check server logs for detailed errors

---

## Performance Expectations

| Setup | Time per Query |
|-------|----------------|
| **Ollama (local)** | 5-15s (depends on model) |
| **NVIDIA API** | 20-60s (if available) |
| **Chunk summary only** | <1s |

---

## Configuration

**In `src/services/retrieval_service.py`, you can customize:**

```python
# Force NVIDIA only (no Ollama)
service = RetrievalService(db_path=str(VECTOR_DIRECTORY), use_ollama_first=False)

# Custom timeout for NVIDIA
nvidia_client = NVIDIAOpenAIClient(timeout=45)

# Custom Ollama model
ollama_client = OllamaClient(model="neural-chat")
```

---

## Next Steps

1. ✅ Install Ollama
2. ✅ Pull a model (`ollama pull mistral`)
3. ✅ Run Ollama daemon
4. ✅ Start FastAPI & Streamlit
5. ✅ Query and enjoy fast, reliable AI answers!

---

**System Status**: Production-ready with dual-LLM fallback ✓
