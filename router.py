from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
from service import create_org_service, upload_file_service, chat_service

router = APIRouter()


class CreateOrgRequest(BaseModel):
    org_id: str
    org_name: str


class ChatRequest(BaseModel):
    org_id: str
    question: str


@router.post("/organizations")
def create_org(payload: CreateOrgRequest):
    return create_org_service(
        org_id=payload.org_id,
        org_name=payload.org_name
    )


@router.post("/upload")
async def upload_file(
    org_id: str = Form(...),
    file: UploadFile = File(...)
):
    return await upload_file_service(
        org_id=org_id,
        file=file
    )


@router.post("/chat")
def chat(payload: ChatRequest):
    return chat_service(
        org_id=payload.org_id,
        question=payload.question
    )