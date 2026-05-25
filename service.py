import os
import tempfile
from dotenv import load_dotenv
from fastapi import UploadFile
from pinecone import Pinecone
from pinecone_plugins.assistant.models.chat import Message

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

pc = Pinecone(api_key=PINECONE_API_KEY)

# Single shared assistant for all organizations
SHARED_ASSISTANT_NAME = "shared-assistant"

# In-memory org store — replace with MongoDB for production
organizations = {"m1"}


def _get_or_create_shared_assistant():
    """
    Returns the shared assistant instance, creating it if it doesn't exist.
    All orgs share this one assistant; isolation is done via metadata filtering.
    """
    try:
        return pc.assistant.Assistant(assistant_name=SHARED_ASSISTANT_NAME)
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
        return pc.assistant.Assistant(assistant_name=SHARED_ASSISTANT_NAME)


def create_org_service(org_id: str, org_name: str):
    if org_id in organizations:
        return {
            "message": "Organization already exists",
            "org_id": org_id,
            "org_name": organizations[org_id]["org_name"],
        }

    organizations[org_id] = {
        "org_id": org_id,
        "org_name": org_name,
    }

    # Ensure the shared assistant exists
    _get_or_create_shared_assistant()

    return {
        "message": "Organization created successfully",
        "org_id": org_id,
        "org_name": org_name,
    }


async def upload_file_service(org_id: str, file: UploadFile):
    if org_id not in organizations:
        return {
            "success": False,
            "error": "Organization not found"
        }

    tmp_path = None

    try:
        assistant = _get_or_create_shared_assistant()
        content = await file.read()

        # Write to a temp file — upload_file is the stable method in plugin 1.4.0
        suffix = f"_{file.filename}"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        # Tag every file with org_id for filtering at chat time
        response = assistant.upload_file(
            file_path=tmp_path,
            metadata={"org_id": org_id},
            timeout=None
        )

        return {
            "success": True,
            "message": "File uploaded successfully",
            "org_id": org_id,
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
    if org_id not in organizations:
        return {
            "success": False,
            "error": "Organization not found"
        }

    try:
        assistant = _get_or_create_shared_assistant()

        msg = Message(role="user", content=question)

        # Filter to only this org's files using metadata
        resp = assistant.chat(
            messages=[msg],
            filter={"org_id": {"$eq": org_id}}
        )

        return {
            "success": True,
            "answer": resp.message.content,
            "citations": resp.citations if hasattr(resp, "citations") else [],
        }

    except Exception as e:
        return {
            "success": False,
            "message": "Chat failed",
            "error": str(e)
        }