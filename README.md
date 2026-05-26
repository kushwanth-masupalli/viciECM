# viciECM — Multi-Org Document Q&A API

A FastAPI backend that lets multiple organizations upload documents and chat with an AI assistant powered by **Pinecone Assistant**. All organizations share a single Pinecone assistant, with file isolation enforced via metadata filtering.

---

## Tech Stack

- **FastAPI** — REST API framework
- **Pinecone** `5.4.2` — Vector database
- **pinecone-plugin-assistant** `1.4.0` — RAG-based assistant
- **Python** `3.11.9`

---

## Setup

### 1. Clone and create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create a `.env` file

```env
PINECONE_API_KEY=your_pinecone_api_key_here
```

### 4. Run the server

```bash
uvicorn main:app --reload
```

Server runs at `http://localhost:8000`  
Swagger UI at `http://localhost:8000/docs`

---

## API Endpoints

### `POST /api/organizations`
Register a new organization. Creates the shared Pinecone assistant if it doesn't exist yet.

**Request body:**
```json
{
  "org_id": "m1",
  "org_name": "Iron Man Corp"
}
```

---

### `POST /api/upload`
Upload a document for a specific organization. Files are tagged with `org_id` metadata for isolation.

**Form data:**
| Field    | Type   | Description          |
|----------|--------|----------------------|
| `org_id` | string | Organization ID      |
| `file`   | file   | PDF or text document |

---

### `POST /api/chat`
Ask a question. The assistant only searches documents belonging to the given `org_id`.

**Request body:**
```json
{
  "org_id": "m1",
  "question": "What are the key skills on this resume?"
}
```

---

## Architecture

```
All orgs → 1 shared Pinecone assistant
           ├── file (org_id: m1) 
           ├── file (org_id: m1)
           ├── file (org_id: m2)
           └── file (org_id: m3)

Chat request for m1 → filter: { org_id: { $eq: "m1" } }
→ Only retrieves m1's files
```

This approach keeps usage within Pinecone's free tier (5 assistant limit) while supporting unlimited organizations.

---

## ⚠️ Known Limitation

The `organizations` store is **in-memory only**. Restarting the server clears all registered orgs, causing `Organization not found` errors even though files still exist in Pinecone.

**Recommended fix:** Persist organizations in MongoDB using `motor`.

---

## Project Structure

```
├── main.py          # FastAPI app entry point
├── router.py        # API route definitions
├── service.py       # Business logic + Pinecone integration
├── requirements.txt # Dependencies
└── .env             # API keys (not committed to git)
```
