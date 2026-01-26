from fastapi import FastAPI
app = FastAPI(title="Crowmind API")

@app.get("/")
def read_root():
    return {"message": "Crowmind Backend FastAPI ready!"}

@app.get("/health")
def health():
    return {"status": "healthy"}

