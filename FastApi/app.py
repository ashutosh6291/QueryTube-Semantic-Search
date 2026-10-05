from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
import faiss
import pickle
import ast
import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

app = FastAPI(title="QueryTube YouTube Semantic Search API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

INDEX_PATH = "models/faiss_index.bin"
META_PATH = "models/metadata.pkl"
TFIDF_PATH = "models/tfidf.pkl"
SVD_PATH = "models/svd.pkl"

index = None
metadata = None
tfidf_vectorizer = None
svd_model = None

os.makedirs("models", exist_ok=True)


def parse_embedding(emb_str):
    if isinstance(emb_str, (list, tuple, np.ndarray)):
        return np.asarray(emb_str, dtype="float32")
    try:
        return np.asarray(ast.literal_eval(str(emb_str)), dtype="float32")
    except Exception:
        values = str(emb_str).strip("[]").split(",")
        return np.asarray([float(x) for x in values if x.strip()], dtype="float32")


def build_faiss_index(df):
    if "text_embedding" not in df.columns:
        raise ValueError("CSV must contain a text_embedding column")
    df = df.copy()
    df["text_embedding"] = df["text_embedding"].apply(parse_embedding)
    embeddings = np.vstack(df["text_embedding"].values).astype("float32")
    index_obj = faiss.IndexFlatL2(embeddings.shape[1])
    index_obj.add(embeddings)

    def row_meta(row):
        return row.to_dict()

    metadata_cols = [c for c in df.columns if c != "text_embedding"]
    return index_obj, df[metadata_cols].to_dict(orient="records")


def save_models(index_obj, meta, tfidf, svd):
    faiss.write_index(index_obj, INDEX_PATH)
    with open(META_PATH, "wb") as f:
        pickle.dump(meta, f)
    with open(TFIDF_PATH, "wb") as f:
        pickle.dump(tfidf, f)
    with open(SVD_PATH, "wb") as f:
        pickle.dump(svd, f)


def load_models():
    global index, metadata, tfidf_vectorizer, svd_model
    if index is None:
        required = [INDEX_PATH, META_PATH, TFIDF_PATH, SVD_PATH]
        if not all(os.path.exists(p) for p in required):
            raise FileNotFoundError("Search models are missing. Ingest the CSV first.")
        index = faiss.read_index(INDEX_PATH)
        with open(META_PATH, "rb") as f:
            metadata = pickle.load(f)
        with open(TFIDF_PATH, "rb") as f:
            tfidf_vectorizer = pickle.load(f)
        with open(SVD_PATH, "rb") as f:
            svd_model = pickle.load(f)


def normalize_result(data, rank, score):
    payload = dict(data)
    return {
        "rank": rank,
        "video_id": data.get("video_id"),
        "title": data.get("title"),
        "channel": data.get("channel_title"),
        "similarity_score": round(float(score), 4),
        "payload": payload,
    }


@app.get("/")
def root():
    return {"message": "QueryTube API is running", "docs": "/docs"}


@app.post("/ingest")
async def ingest_data(file: UploadFile = File(...)):
    try:
        df = pd.read_csv(file.file)
        if "transcript" in df.columns:
            df["transcript"] = df["transcript"].fillna("")
        index_obj, meta = build_faiss_index(df)

        combined = df.get("title", "").astype(str) + " " + df.get("transcript", "").astype(str)
        tfidf = TfidfVectorizer(stop_words="english", max_features=5000)
        X = tfidf.fit_transform(combined)
        n_components = max(1, min(100, X.shape[0] - 1, X.shape[1] - 1)) if min(X.shape) > 1 else 1
        svd = TruncatedSVD(n_components=n_components, random_state=42)
        svd.fit(X)

        global index, metadata, tfidf_vectorizer, svd_model
        index, metadata, tfidf_vectorizer, svd_model = index_obj, meta, tfidf, svd
        save_models(index_obj, meta, tfidf, svd)
        return {"message": "Data ingested successfully", "status": "success", "records": len(df), "rows_inserted": len(df)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/ingest_csv")
async def ingest_csv(file: UploadFile = File(...)):
    return await ingest_data(file)


@app.get("/search")
async def search_videos(query: str, k: int = 5):
    try:
        load_models()
        query_tfidf = tfidf_vectorizer.transform([query])
        query_emb = svd_model.transform(query_tfidf).astype("float32")
        distances, indices = index.search(query_emb, k)
        scores = 1 / (1 + distances[0])
        results = []
        for rank, i in enumerate(indices[0]):
            if i < 0 or i >= len(metadata):
                continue
            results.append(normalize_result(metadata[i], rank + 1, scores[rank]))
        return {"query": query, "results": results}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/search")
async def search_videos_post(body: dict):
    query = str(body.get("query", "")).strip()
    k = int(body.get("top_k", body.get("k", 8)))
    if not query:
        return JSONResponse(status_code=400, content={"error": "query is required"})
    return await search_videos(query, k)


@app.post("/summarize")
async def summarize_video(body: dict):
    text = str(body.get("transcript") or body.get("combined_text") or body.get("description") or "").strip()
    title = str(body.get("title") or "Video Summary")
    if not text:
        return {"summary": f"No transcript or description is available for: {title}"}
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    summary = " ".join(sentences[:5])
    return {"summary": summary[:1500]}
