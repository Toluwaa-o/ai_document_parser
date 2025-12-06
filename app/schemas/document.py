from pydantic import BaseModel

class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    message: str


class DocumentAnalysisResponse(BaseModel):
    id: str
    summary: str
    document_type: str
    metadata: dict


class DocumentResponse(BaseModel):
    id: str
    filename: str
    extracted_text: str
    summary: str
    document_type: str
    metadata: dict
    created_at: str
    analyzed_at: str

    class Config:
        from_attributes = True