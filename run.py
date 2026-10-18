"""
PriceCraft AI - Local Development Runner
"""

import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("  Starting PriceCraft AI Server on http://127.0.0.1:8000")
    print("  Powered by Prior Labs TabPFN & Google Gemma 2")
    print("=" * 60)
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
