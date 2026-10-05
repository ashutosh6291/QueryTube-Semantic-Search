
# 🎥 YouTube Vector Search API (FastAPI + FAISS + TF-IDF + SVD)

This project implements a **YouTube Video Semantic Search API** using **FastAPI**, **FAISS**, and **Scikit-Learn** for vectorization.  
It allows you to upload a CSV containing YouTube video data with precomputed embeddings and then perform **semantic search** on titles and transcripts.

---

## 🚀 Features
- ✅ Upload CSV and build FAISS index  
- ✅ Store and load TF-IDF + SVD vectorizer models  
- ✅ Search semantically similar videos by query text  
- ✅ Simple REST API endpoints for ingestion and retrieval  

---

## 🧩 Tech Stack
- **FastAPI**
- **FAISS**
- **Scikit-learn**
- **Pandas / NumPy**
- **Uvicorn**

---

## 📁 Project Structure
```
app.py                                # Main FastAPI app
models/                               # Folder for FAISS index and model files
youtube_details_with_embeddings.csv    # Input CSV file
```

---

## ⚙️ Installation & Setup

```bash
# Create a virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn faiss-cpu scikit-learn pandas numpy
```

---

## ▶️ Run the App

```bash
uvicorn app:app --reload
```

Your FastAPI app will start running at:  
👉 **http://127.0.0.1:8000**

---

## 📤 Ingest Data

Use **PowerShell** (Windows) to upload your YouTube CSV file:

```bash
Invoke-RestMethod -Uri "http://127.0.0.1:8000/ingest" -Method POST -Form @{
    file = Get-Item ".\youtube_details_with_embeddings.csv"
}
```

You should see:
```
✅ Data ingested successfully
```

---

## 🔍 Search Videos

You can perform semantic search using:

```bash
curl "http://127.0.0.1:8000/search?query=artificial+intelligence&k=5"
```

Response example:
```json
{
  "query": "artificial intelligence",
  "results": [
    {
      "rank": 1,
      "video_id": "abc123",
      "title": "AI in Everyday Life",
      "channel": "Tech Explained",
      "similarity_score": 0.9421
    }
  ]
}
```

---

## 👨‍💻 Author
**Developed by M SHALOM VISHAL**
