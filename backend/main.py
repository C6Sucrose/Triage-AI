from fastapi import FastAPI

app = FastAPI(title="Triage AI Backend")

@app.get("/")
def read_root():
    return {"status": "Backend is running!"}