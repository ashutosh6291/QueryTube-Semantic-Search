from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
import faiss
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
import os

app = FastAPI(title="YouTube Vector Search API")

# ============================================================
# 1️⃣ Global Variables
# ============================================================
INDEX_PATH = "models/faiss_index.bin"
META_PATH = "models/metadata.pkl"
TFIDF_PATH = "models/tfidf.pkl"
SVD_PATH = "models/svd.pkl"

index = None
metadata = None
tfidf_vectorizer = None
svd_model = None

os.makedirs("models", exist_ok=True)


# ============================================================
# 2️⃣ Helper Functions
# ============================================================
def parse_embedding(emb_str):
    try:
        return np.array(eval(emb_str), dtype="float32")
    except Exception:
        emb_str = emb_str.strip("[]")
        return np.array([float(x) for x in emb_str.split(",")], dtype="float32")


def build_faiss_index(df):
    df["text_embedding"] = df["text_embedding"].apply(parse_embedding)
    embeddings = np.vstack(df["text_embedding"].values).astype("float32")
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index, df[["video_id", "title", "channel_title"]].to_dict(orient="records")


# ============================================================
# 3️⃣ API: Upload CSV + Build Vector Index
# ============================================================
@app.post("/ingest")
async def ingest_data(file: UploadFile):
    try:
        df = pd.read_csv(file.file)
        df["transcript"] = df["transcript"].fillna("")
        index, meta = build_faiss_index(df)

        # Save FAISS and metadata
        faiss.write_index(index, INDEX_PATH)
        with open(META_PATH, "wb") as f:
            pickle.dump(meta, f)

        # Train TF-IDF + SVD
        df["combined_text"] = df["title"].astype(str) + " " + df["transcript"].astype(str)
        tfidf = TfidfVectorizer(stop_words="english", max_features=5000)
        X = tfidf.fit_transform(df["combined_text"])
        svd = TruncatedSVD(n_components=100, random_state=42)
        svd.fit(X)

        # Save models
        with open(TFIDF_PATH, "wb") as f:
            pickle.dump(tfidf, f)
        with open(SVD_PATH, "wb") as f:
            pickle.dump(svd, f)

        return {"message": "✅ Data ingested successfully", "records": len(df)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ============================================================
# 4️⃣ API: Search Query
# ============================================================
@app.get("/search")
async def search_videos(query: str, k: int = 5):
    global index, metadata, tfidf_vectorizer, svd_model

    if not all([os.path.exists(INDEX_PATH), os.path.exists(META_PATH)]):
        return JSONResponse(status_code=400, content={"error": "No FAISS index found. Please ingest data first."})

    if index is None:
        index = faiss.read_index(INDEX_PATH)
        with open(META_PATH, "rb") as f:
            metadata = pickle.load(f)
        with open(TFIDF_PATH, "rb") as f:
            tfidf_vectorizer = pickle.load(f)
        with open(SVD_PATH, "rb") as f:
            svd_model = pickle.load(f)

    # Encode query
    query_tfidf = tfidf_vectorizer.transform([query])
    query_emb = svd_model.transform(query_tfidf).astype("float32")

    distances, indices = index.search(query_emb, k)
    scores = 1 / (1 + distances[0])

    results = []
    for rank, i in enumerate(indices[0]):
        data = metadata[i]
        results.append({
            "rank": rank + 1,
            "video_id": data.get("video_id"),
            "title": data.get("title"),
            "channel": data.get("channel_title"),
            "similarity_score": round(float(scores[rank]), 4)
        })

    return {"query": query, "results": results}
