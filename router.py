from fastapi import APIRouter, UploadFile, File, Form, Depends
from pydantic import BaseModel

from service import upload_file_service, chat_service
from auth_service import (
    org_signup_service,
    signin_service,
    get_current_user,
    check_org_access
)

router = APIRouter()


class OrgSignupRequest(BaseModel):
    email: str
    password: str
    org_id: str
    org_name: str


class SigninRequest(BaseModel):
    email: str
    password: str


class ChatRequest(BaseModel):
    org_id: str
    question: str


@router.post("/auth/org-signup")
def org_signup(payload: OrgSignupRequest):
    return org_signup_service(
        email=payload.email,
        password=payload.password,
        org_id=payload.org_id,
        org_name=payload.org_name
    )


@router.post("/auth/signin")
def signin(payload: SigninRequest):
    return signin_service(
        email=payload.email,
        password=payload.password
    )


@router.post("/upload")
async def upload_file(
    org_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    check_org_access(org_id, current_user)

    return await upload_file_service(
        org_id=org_id,
        file=file
    )


@router.post("/chat")
def chat(
    payload: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    check_org_access(payload.org_id, current_user)

    return chat_service(
        org_id=payload.org_id,
        question=payload.question
    )