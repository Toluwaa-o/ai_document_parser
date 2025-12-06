from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Header
from app.schemas.document import DocumentAnalysisResponse, DocumentResponse, DocumentUploadResponse
from app.utils.document import extract_text_from_pdf, upload_to_minio, analyze_with_openrouter
from app.db.base import Document, SessionLocal
from fastapi import UploadFile, File, HTTPException, BackgroundTasks
import uuid
import json
from datetime import datetime

router = APIRouter(prefix="/documents", tags=["Documents"])

MAX_FILE_SIZE = 5 * 1024 * 1024


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and extract text from PDF document"""

    # Validate file type
    if file.content_type not in ["application/pdf", "text/plain"]:
        raise HTTPException(
            status_code=400, detail="Only PDF files are supported")

    # Validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, detail=f"File size exceeds {MAX_FILE_SIZE} bytes")

    # Extract text
    try:
        extracted_text = extract_text_from_pdf(content)
        if not extracted_text:
            raise HTTPException(
                status_code=400, detail="No text could be extracted from PDF")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Upload to Minio
    try:
        file_path = upload_to_minio(content, file.filename)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Save to database
    db = SessionLocal()
    try:
        doc_id = str(uuid.uuid4())
        document = Document(
            id=doc_id,
            filename=file.filename,
            file_path=file_path,
            extracted_text=extracted_text
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        return DocumentUploadResponse(
            id=document.id,
            filename=document.filename,
            message="Document uploaded and text extracted successfully"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()


@router.post("/{doc_id}/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document(doc_id: str, background_tasks: BackgroundTasks):
    """Analyze document with LLM and extract metadata"""

    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == doc_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if not document.extracted_text:
            raise HTTPException(status_code=400, detail="No text to analyze")

        # Analyze with OpenRouter
        try:
            analysis_result = await analyze_with_openrouter(document.extracted_text)
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))

        # Update document with analysis results
        document.summary = analysis_result.get("summary", "")
        document.document_type = analysis_result.get(
            "document_type", "unknown")
        document.metadata_info = json.dumps(analysis_result.get("metadata", {}))
        document.analyzed_at = datetime.utcnow()

        db.commit()
        db.refresh(document)

        return DocumentAnalysisResponse(
            id=document.id,
            summary=document.summary,
            document_type=document.document_type,
            metadata=json.loads(document.metadata_info)
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Analysis error: {str(e)}")
    finally:
        db.close()


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str):
    """Retrieve complete document information"""

    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == doc_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            extracted_text=document.extracted_text,
            summary=document.summary or "",
            document_type=document.document_type or "",
            metadata=json.loads(
                document.metadata_info) if document.metadata_info else {},
            created_at=document.created_at.isoformat(),
            analyzed_at=document.analyzed_at.isoformat() if document.analyzed_at else ''
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Retrieval error: {str(e)}")
    finally:
        db.close()
