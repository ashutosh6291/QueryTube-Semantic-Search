# QueryTube Semantic Search

AI-powered semantic search application for YouTube videos using NLP, embeddings, vector search, FastAPI and React.

## Contributors

- Ashutosh Ranjan
- Saloni Singh

## What this project does

QueryTube builds a semantic search pipeline for YouTube content. It works with video metadata and transcripts, creates/searches vector representations, and returns relevant videos for natural-language queries.

## Project structure

```text
QueryTube-Semantic-Search/
├── FastApi/                 # FastAPI + FAISS backend and pretrained index/models
├── frontend/                # React/Vite frontend
├── models/                  # Search model files are inside FastApi/models
├── yt_data.py               # YouTube metadata collection
├── transcripts.py           # Transcript extraction/processing
├── embed.py                 # Embedding generation
├── vector_db.py             # Vector database utilities
├── App.jsx                  # Original frontend source
├── VideoSummaryModal.jsx    # Original summary modal
├── requirements.txt         # Python dependencies
└── LICENSE                  # Original MIT license
```

## Run the backend

From `FastApi`:

```bash
python -m venv venv
# Windows PowerShell
.\venv\Scripts\Activate.ps1
pip install -r ..\requirements.txt
uvicorn app:app --reload
```

API: http://127.0.0.1:8000
Swagger: http://127.0.0.1:8000/docs

## Run the frontend

From `frontend`:

```bash
npm install
npm run dev
```

Frontend: http://localhost:5173

## Notes

The repository retains the original project data, model files and MIT license. Do not commit API keys or `.env` files.

The original project specification covers YouTube data collection, transcript extraction, SentenceTransformer evaluation, vector indexing, semantic retrieval and deployment.
