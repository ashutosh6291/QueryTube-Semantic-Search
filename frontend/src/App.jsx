import { useState } from "react";
import VideoSummaryModal from "./VideoSummaryModal";

function App() {
  const API = "http://127.0.0.1:8000";

  const [activeTab, setActiveTab] = useState("search");

  // SEARCH STATES
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  // SUMMARY STATES
  const [summaryModalOpen, setSummaryModalOpen] = useState(false);
  const [currentVideoTitle, setCurrentVideoTitle] = useState("");
  const [currentSummary, setCurrentSummary] = useState("");
  const [summaryLoading, setSummaryLoading] = useState(false);

  // INGEST STATES
  const [csvFile, setCsvFile] = useState(null);
  const [ingestMessage, setIngestMessage] = useState("");

  // -----------------------------
  // SEARCH
  // -----------------------------
  const handleSearch = async () => {
    setLoading(true);
    setResults([]);

    try {
      const resp = await fetch(`${API}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, top_k: 8 }),
      });

      const data = await resp.json();
      setResults(data.results || []);
    } catch (err) {
      console.error("Search error:", err);
      alert("Search failed — check backend logs / network.");
    } finally {
      setLoading(false);
    }
  };

  // -----------------------------
  // SUMMARY
  // -----------------------------
  const summarize = async (video) => {
    const vid = video.payload || {};

    setSummaryModalOpen(true);
    setCurrentVideoTitle(vid.title || "Video Summary");
    setCurrentSummary("");
    setSummaryLoading(true);

    const body = {
      title: vid.title,
      transcript: vid.transcript || "",
      combined_text: vid.combined_text || vid.description || "",
      description: vid.description || "",
    };

    try {
      const resp = await fetch(`${API}/summarize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!resp.ok) {
        const errorBody = await resp.text();
        throw new Error(`Summarize returned ${resp.status} — ${errorBody}`);
      }

      const data = await resp.json();
      setCurrentSummary(data.summary || data.error || "Summary not available.");
    } catch (err) {
      console.error("Summarize error:", err);
      setCurrentSummary(`Error generating summary: ${err.message}`);
    } finally {
      setSummaryLoading(false);
    }
  };

  // -----------------------------
  // CSV INGEST
  // -----------------------------
  const uploadCSV = async () => {
    if (!csvFile) return alert("Please select a CSV file first.");

    const formData = new FormData();
    formData.append("file", csvFile);

    setIngestMessage("Uploading...");

    try {
      const resp = await fetch(`${API}/ingest_csv`, {
        method: "POST",
        body: formData,
      });

      const data = await resp.json();

      if (data.status === "success") {
        setIngestMessage(`✅ CSV uploaded successfully (${data.rows_inserted} rows)`);
      } else {
        // show server-side error message when available
        const err = data.error || data.message || JSON.stringify(data);
        setIngestMessage(`❌ Upload failed: ${err}`);
      }
    } catch (err) {
      console.error("Upload error:", err);
      setIngestMessage(`❌ Upload failed: ${err.message}`);
    }
  };

  // helper to render metadata field with fallback
  const md = (value) => (value === undefined || value === null ? "N/A" : value);

  // -----------------------------
  // RENDER UI
  // -----------------------------
  return (
    <div style={{ color: "white", background: "#0f0f0f", minHeight: "100vh", padding: "20px" }}>
      
      {/* TABS */}
      <div style={{ textAlign: "center", marginBottom: "20px" }}>
        <button
          onClick={() => setActiveTab("search")}
          style={{
            padding: "10px 20px",
            marginRight: "10px",
            background: activeTab === "search" ? "red" : "#333",
            color: "white",
            borderRadius: "6px",
            border: "none",
            cursor: "pointer",
          }}
        >
          🔍 Search
        </button>

        <button
          onClick={() => setActiveTab("ingest")}
          style={{
            padding: "10px 20px",
            background: activeTab === "ingest" ? "green" : "#333",
            color: "white",
            borderRadius: "6px",
            border: "none",
            cursor: "pointer",
          }}
        >
          📥 Ingest CSV
        </button>
      </div>

      {/* ----------------------------------------- */}
      {/* SEARCH TAB */}
      {/* ----------------------------------------- */}
      {activeTab === "search" && (
        <div>
          <h1 style={{ color: "red", textAlign: "center" }}>YouTube Semantic Search</h1>

          <div style={{ textAlign: "center", marginTop: "20px" }}>
            <input
              type="text"
              placeholder="Search videos..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              style={{
                width: "50%",
                padding: "12px",
                borderRadius: "8px",
                background: "#222",
                border: "1px solid #444",
                color: "white",
              }}
            />
            <button
              onClick={handleSearch}
              style={{
                marginLeft: "10px",
                padding: "12px 20px",
                background: "red",
                borderRadius: "8px",
                border: "none",
                cursor: "pointer",
              }}
            >
              {loading ? "Searching…" : "Search"}
            </button>
          </div>

          {/* RESULTS */}
          <div style={{ marginTop: "40px" }}>
            {results.map((item, idx) => {
              const vid = item.payload || {};

              // select thumbnail (try a few common payload keys)
              const thumbnail = vid.thumbnail_high || vid.thumbnail_default || vid.thumbnail || "";

              return (
                <div
                  key={idx}
                  style={{
                    background: "#1a1a1a",
                    marginBottom: "20px",
                    padding: "20px",
                    borderRadius: "10px",
                    display: "flex",
                    gap: "20px",
                    alignItems: "flex-start",
                  }}
                >
                  {/* Thumbnail */}
                  <div style={{ flex: "0 0 240px" }}>
                    {thumbnail ? (
                      <img
                        src={thumbnail}
                        alt="Thumbnail"
                        style={{ width: "240px", height: "135px", borderRadius: "8px", objectFit: "cover" }}
                      />
                    ) : (
                      <div
                        style={{
                          width: "240px",
                          height: "135px",
                          borderRadius: "8px",
                          background: "#2a2a2a",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          color: "#888",
                        }}
                      >
                        No thumbnail
                      </div>
                    )}
                  </div>

                  <div style={{ flex: 1 }}>
                    <h2 style={{ color: "red", margin: 0 }}>{vid.title || "Untitled"}</h2>

                    <p style={{ opacity: 0.85, marginTop: "8px" }}>
                      {vid.description ? vid.description.slice(0, 200) : "No description available."}
                    </p>

                    {/* METADATA BLOCK */}
                    <div style={{ fontSize: "14px", color: "#ccc", marginTop: "12px", lineHeight: "1.6", display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))", gap: "6px 18px" }}>
                      <div><b>Published:</b> {md(vid.publishedAt)}</div>
                      <div><b>Default Language:</b> {md(vid.defaultLanguage)}</div>
                      <div><b>Audio Language:</b> {md(vid.defaultAudioLanguage || vid.defaultAudio)}</div>
                      <div><b>Duration:</b> {vid.duration_seconds ? `${vid.duration_seconds} sec` : md(vid.duration)}</div>

                      <div><b>Views:</b> {md(vid.viewCount ?? vid.views ?? 0)}</div>
                      <div><b>Likes:</b> {md(vid.likeCount ?? vid.likes ?? 0)}</div>
                      <div><b>Comments:</b> {md(vid.commentCount ?? vid.comments ?? 0)}</div>
                      <div><b>Transcript:</b> { (vid.transcript_available || vid.is_transcript_available || vid.transcript) ? "Yes" : "No" }</div>

                      <div><b>Channel Country:</b> {md(vid.channel_country)}</div>
                      <div><b>Channel Subscribers:</b> {md(vid.channel_subscriberCount ?? vid.channel_subscribers ?? 0)}</div>
                    </div>

                    {/* ACTIONS */}
                    <div style={{ marginTop: "12px" }}>
                      <button
                        onClick={() => summarize(item)}
                        style={{
                          padding: "8px 15px",
                          borderRadius: "6px",
                          background: "#333",
                          color: "white",
                          marginRight: "10px",
                          border: "1px solid #444",
                          cursor: "pointer",
                        }}
                      >
                        📄 Summarize
                      </button>

                      <a
                        href={`https://www.youtube.com/watch?v=${vid.video_id || vid.videoId || vid.videoIdStr || ""}`}
                        target="_blank"
                        rel="noreferrer"
                        style={{
                          padding: "8px 15px",
                          background: "#0057ff",
                          borderRadius: "6px",
                          color: "white",
                          textDecoration: "none",
                        }}
                      >
                        ▶ Watch
                      </a>
                    </div>
                  </div>
                </div>
              );
            })}

            {results.length === 0 && (
              <div style={{ color: "#bbb", textAlign: "center", padding: "30px 0" }}>
                No results yet — try a different query.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ----------------------------------------- */}
      {/* INGEST TAB */}
      {/* ----------------------------------------- */}
      {activeTab === "ingest" && (
        <div style={{ maxWidth: "700px", margin: "auto", textAlign: "center", paddingTop: "40px" }}>
          <h2 style={{ color: "lightgreen" }}>Upload CSV to Qdrant</h2>

          <input
            type="file"
            accept=".csv"
            onChange={(e) => setCsvFile(e.target.files[0])}
            style={{ marginTop: "20px" }}
          />

          <button
            onClick={uploadCSV}
            style={{
              marginTop: "20px",
              padding: "12px 20px",
              background: "green",
              borderRadius: "8px",
              border: "none",
              color: "white",
              cursor: "pointer",
            }}
          >
            Upload CSV
          </button>

          <p style={{ marginTop: "20px", color: ingestMessage.startsWith("✅") ? "#9be49b" : "lightgreen" }}>
            {ingestMessage}
          </p>
        </div>
      )}

      {/* SUMMARY MODAL */}
      <VideoSummaryModal
        visible={summaryModalOpen}
        onClose={() => setSummaryModalOpen(false)}
        title={currentVideoTitle}
        summary={currentSummary}
        loading={summaryLoading}
      />
    </div>
  );
}

export default App;
