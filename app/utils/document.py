from openai import OpenAI
import PyPDF2
from io import BytesIO
from app.minio.minio import minio_client
import uuid
from minio.error import S3Error
import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()

BUCKET = "ai-document-parser"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"


client = OpenAI(
    base_url=OPENROUTER_API_BASE,
    api_key=OPENROUTER_API_KEY,
)


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF using PyPDF2"""
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()

        print(f"Text Extracted: {text.strip()}")
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")


def upload_to_minio(file_content: bytes, file_name: str) -> str:
    """Upload file to Minio and return file path"""
    if not minio_client:
        raise RuntimeError("Minio client not initialized")

    try:
        file_id = str(uuid.uuid4())
        object_name = f"documents/{file_id}/{file_name}"

        minio_client.put_object(
            BUCKET,
            object_name,
            BytesIO(file_content),
            length=len(file_content)
        )
        print("Document uploaded to Minio")
        return object_name
    except S3Error as e:
        raise RuntimeError(f"Failed to upload to Minio: {str(e)}")


async def analyze_with_openrouter(text: str) -> dict:
    """Send text to OpenRouter LLM and extract summary, type, and metadata"""

    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not configured")

    prompt = f"""Analyze the following document and provide:
                1. A concise summary (2-3 sentences)
                2. Document type (invoice, CV, report, letter, contract, email, other)
                3. Extracted metadata in JSON format

                For metadata, extract relevant fields like:
                - date (if present)
                - sender/from
                - recipient/to
                - total_amount (if it's an invoice)
                - key_entities (persons, organizations, locations)
                - subject (if applicable)

                Document text:
                ---
                {text[:8000]}
                ---

                Respond in this exact JSON format:
                {{
                    "summary": "...",
                    "document_type": "...",
                    "metadata": {{
                        "date": "...",
                        "sender": "...",
                        "recipient": "...",
                        "total_amount": "...",
                        "key_entities": ["..."],
                        "subject": "..."
                    }}
                }}
            """

    try:
        completion = client.chat.completions.create(
            model="google/gemini-2.5-flash-lite",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )

        content = completion.choices[0].message.content

        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        if json_start != -1 and json_end > json_start:
            json_str = content[json_start:json_end]
            return json.loads(json_str)
        else:
            raise ValueError("Could not parse JSON from LLM response")

    except httpx.HTTPError as e:
        raise RuntimeError(f"OpenRouter API error: {str(e)}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse LLM response: {str(e)}")
