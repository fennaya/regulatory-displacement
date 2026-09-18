"""Run the Displacement Observatory dashboard locally."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("displacement_observatory.dashboard.app:app", host="127.0.0.1", port=8420, reload=False)
