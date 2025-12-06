import os
import minio
from dotenv import load_dotenv

load_dotenv()

ENDPOINT = os.getenv("ENDPOINT")
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
BUCKET = "ai-document-parser"

try:
    minio_client = minio.Minio(
        ENDPOINT,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        secure=True
    )

    if not minio_client.bucket_exists(BUCKET):
        minio_client.make_bucket(BUCKET)
except Exception as e:
    print(f"Warning: Minio connection failed: {e}")
    minio_client = None
