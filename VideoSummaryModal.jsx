import React from "react";

function VideoSummaryModal({ visible, onClose, title, summary, loading }) {
  if (!visible) return null;

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100vw",
        height: "100vh",
        background: "rgba(0,0,0,0.75)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 9999,
      }}
    >
      <div
        style={{
          background: "#1c1c1e",
          width: "60%",
          maxWidth: "700px",
          padding: "30px",
          borderRadius: "12px",
          color: "white",
          boxShadow: "0 0 40px rgba(0,0,0,0.5)",
          animation: "fadeIn 0.3s ease",
        }}
      >
        {/* Title */}
        <h2 style={{ marginBottom: "15px", fontSize: "22px", fontWeight: "600" }}>
          {title}
        </h2>

        {/* Divider */}
        <div
          style={{
            width: "100%",
            height: "1px",
            background: "#444",
            marginBottom: "20px",
          }}
        ></div>

        {/* Loading spinner */}
        {loading ? (
          <div style={{ textAlign: "center", padding: "20px" }}>
            <div className="spinner"></div>
            <p style={{ marginTop: "10px" }}>Generating summary...</p>
          </div>
        ) : (
          <p style={{ lineHeight: "1.6", whiteSpace: "pre-wrap" }}>
            {summary || "Summary not available."}
          </p>
        )}

        {/* Close Button */}
        <div style={{ textAlign: "center", marginTop: "25px" }}>
          <button
            onClick={onClose}
            style={{
              background: "red",
              padding: "10px 24px",
              borderRadius: "8px",
              border: "none",
              color: "white",
              cursor: "pointer",
              fontSize: "16px",
            }}
          >
            Close
          </button>
        </div>
      </div>

      {/* Spinner CSS */}
      <style>
        {`
          .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #555;
            border-top-color: #ff4747;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: auto;
          }

          @keyframes spin {
            to { transform: rotate(360deg); }
          }

          @keyframes fadeIn {
            from { opacity: 0; transform: scale(0.95); }
            to { opacity: 1; transform: scale(1); }
          }
        `}
      </style>
    </div>
  );
}

export default VideoSummaryModal;
