"""Local entry point for the Trading Robot App 2.0."""

from __future__ import annotations

import uvicorn


if __name__ == "__main__":
    uvicorn.run(
        "app.server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
