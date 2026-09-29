"""
Convenient entrypoint to run the VentureIQ backend server directly with Python:
    python run.py
"""

import os
import sys
import uvicorn

if __name__ == "__main__":
    # Ensure backend directory is in python path
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    os.chdir(backend_dir)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
