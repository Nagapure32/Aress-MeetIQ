# ChromaDB Vector Store

The backend can use either Azure AI Search or ChromaDB for meeting transcript vector search.
Azure OpenAI is still used for embeddings and chat completions.

## Provider Switch

Keep Azure AI Search active until ChromaDB is deployed and existing meetings are re-indexed:

```env
VECTOR_STORE_PROVIDER=azure
```

Switch to ChromaDB after the Chroma service is reachable:

```env
VECTOR_STORE_PROVIDER=chroma
CHROMA_HOST=localhost
CHROMA_PORT=8001
CHROMA_SSL=false
CHROMA_COLLECTION=meeting-transcript-chunks
```

## Local ChromaDB

Run ChromaDB as a separate service with persistent storage. Example:

```powershell
docker run --rm `
  --name meetiq-chroma `
  -p 8001:8000 `
  -v ${PWD}\chroma-data:/chroma/chroma `
  chromadb/chroma
```

Then restart the FastAPI backend so it reloads `.env`.

## Re-indexing

Azure AI Search vectors do not automatically move to ChromaDB. Re-index each meeting after
switching providers:

```http
POST /api/v1/meetings/{meeting_id}/chat/index
```

Uploaded recordings also call the same indexing function, so new uploads will write to the
active provider.

## Rollback

If ChromaDB is unavailable or search quality needs more tuning, set:

```env
VECTOR_STORE_PROVIDER=azure
```

Restart the backend. Existing Azure AI Search indexes remain untouched.
