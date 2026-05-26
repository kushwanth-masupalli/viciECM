import os
import tempfile
from dotenv import load_dotenv
from fastapi import UploadFile
from pinecone import Pinecone
from pinecone_plugins.assistant.models.chat import Message

from database import supabase_admin

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

pc = Pinecone(api_key=PINECONE_API_KEY)

# Single shared assistant for all organizations
SHARED_ASSISTANT_NAME = "shared-assistant"


def _get_or_create_shared_assistant():
    """
    Returns the shared assistant instance, creating it if it doesn't exist.
    All organizations share one Pinecone assistant.
    File isolation is done using metadata filtering with org_id.
    """
    try:
        return pc.assistant.Assistant(
            assistant_name=SHARED_ASSISTANT_NAME
        )

    except Exception:
        pc.assistant.create_assistant(
            assistant_name=SHARED_ASSISTANT_NAME,
            instructions=(
                "You are a helpful assistant. "
                "Answer only from the uploaded documents relevant to the user's organization. "
                "If the answer is not available in the documents, say it is not available."
            ),
            timeout=30
        )

        return pc.assistant.Assistant(
            assistant_name=SHARED_ASSISTANT_NAME
        )


def get_org_from_supabase(org_id: str):
    """
    Checks whether the organization exists in Supabase.
    """
    result = (
        supabase_admin
        .table("organizations")
        .select("*")
        .eq("org_id", org_id)
        .execute()
    )

    if not result.data:
        return None

    return result.data[0]


async def upload_file_service(org_id: str, file: UploadFile):
    """
    Uploads a file to the shared Pinecone assistant.
    File is tagged with org_id metadata.
    """
    org = get_org_from_supabase(org_id)

    if not org:
        return {
            "success": False,
            "error": "Organization not found"
        }

    tmp_path = None

    try:
        assistant = _get_or_create_shared_assistant()

        content = await file.read()

        suffix = f"_{file.filename}"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        response = assistant.upload_file(
            file_path=tmp_path,
            metadata={"org_id": org_id},
            timeout=None
        )

        return {
            "success": True,
            "message": "File uploaded successfully",
            "org_id": org_id,
            "org_name": org["org_name"],
            "file_name": file.filename,
            "pinecone_response": str(response)
        }

    except Exception as e:
        return {
            "success": False,
            "message": "File upload failed",
            "error": str(e)
        }

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def chat_service(org_id: str, question: str):
    """
    Sends a question to Pinecone Assistant.
    Uses org_id metadata filter so only that organization's files are searched.
    """
    org = get_org_from_supabase(org_id)

    if not org:
        return {
            "success": False,
            "error": "Organization not found"
        }

    try:
        assistant = _get_or_create_shared_assistant()

        msg = Message(role="user", content=question)

        response = assistant.chat(
            messages=[msg],
            filter={"org_id": {"$eq": org_id}}
        )

        return {
            "success": True,
            "org_id": org_id,
            "org_name": org["org_name"],
            "question": question,
            "answer": response.message.content,
            "citations": response.citations if hasattr(response, "citations") else []
        }

    except Exception as e:
        return {
            "success": False,
            "message": "Chat failed",
            "error": str(e)
        }