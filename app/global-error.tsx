"use client";

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body style={{ margin: 0, background: "#0d1117", fontFamily: "system-ui, sans-serif" }}>
        <div style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "24px",
        }}>
          <div style={{
            background: "#161b22",
            border: "1px solid #21262d",
            borderRadius: "12px",
            padding: "32px",
            maxWidth: "400px",
            width: "100%",
            textAlign: "center",
          }}>
            <div style={{
              width: "48px",
              height: "48px",
              borderRadius: "50%",
              background: "rgba(248,81,73,0.1)",
              border: "1px solid rgba(248,81,73,0.3)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 16px",
            }}>
              <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="#f85149">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
              </svg>
            </div>
            <h2 style={{ color: "#fff", fontWeight: 600, fontSize: "18px", margin: "0 0 8px" }}>
              Something went wrong
            </h2>
            <p style={{ color: "#6e7681", fontSize: "14px", margin: "0 0 24px", lineHeight: 1.5 }}>
              The dashboard encountered an error. Click below to reload.
            </p>
            <button
              onClick={() => window.location.reload()}
              style={{
                width: "100%",
                background: "#238636",
                color: "#fff",
                fontWeight: 600,
                fontSize: "14px",
                padding: "10px",
                borderRadius: "8px",
                border: "none",
                cursor: "pointer",
              }}
            >
              Reload Dashboard
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
