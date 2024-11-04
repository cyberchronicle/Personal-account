from fastapi import FastAPI, UploadFile
from app.core.s3 import upload_file_to_s3

app = FastAPI()


@app.get("/")
def read_root() -> dict:
    return {"Hello": "World"}


@app.post("/upload")
def upload_file(file: UploadFile) -> None:
    upload_file_to_s3(file)
