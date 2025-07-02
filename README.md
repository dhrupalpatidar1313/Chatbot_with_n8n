# N8N ChatBoat

A full-stack AI-powered chat application with authentication, session management, and persistent chat history. The backend is built with FastAPI, SQLAlchemy, and PostgreSQL, and the frontend is powered by Streamlit. AI responses are fetched via a configurable n8n webhook URL.

---

## Features
- User registration, login, and logout (JWT-based authentication)
- Token blacklisting for secure logout
- Chat sessions and persistent message history
- AI-powered chat (responses via n8n webhook)
- Streamlit web UI for chat
- RESTful API for integration

---

## Tech Stack
- **Backend:** FastAPI, SQLAlchemy, Alembic
- **Frontend:** Streamlit
- **Database:** PostgreSQL (configurable)
- **AI Integration:** n8n Webhook (URL configurable via environment variable)

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <repo-url>
cd N8N_ChatBoat
```

### 2. Create and Configure Environment Variables
Create a `.env` file in the root directory with the following variables:

```
# Database
DATABASE_URL=postgresql://username:password@localhost/dbname

# JWT Secret
SECRET_KEY=your-secret-key-here

# AI Webhook (n8n)
AI_WEBHOOK_URL=https://your-n8n-instance/webhook/ai-chat
WEBHOOK_TIMEOUT=300

# API Base URL for Streamlit (optional)
API_BASE_URL=http://localhost:8000
```

### 3. Install Dependencies
Python 3.12+ is required.

```bash
pip install -r requirements.txt
# or, if using uv
uv pip install -r pyproject.toml
```

### 4. Run Database Migrations (if using Alembic)
```bash
alembic upgrade head
```

### 5. Start the FastAPI Backend
```bash
uvicorn main:app --reload
```

### 6. Start the Streamlit Frontend
```bash
streamlit run app/streamlit_app.py
```

---

## API Overview

### Authentication
- `POST /register` — Register a new user
- `POST /login` — Obtain JWT access token
- `POST /logout` — Blacklist current token
- `GET /me` — Get current user info

### Chat
- `POST /chat/session` — Create a new chat session
- `GET /chat/sessions` — List user chat sessions
- `POST /chat/message` — Send a message and get AI response
- `GET /chat/history/{session_id}` — Get chat history for a session

All chat endpoints require authentication (Bearer token).

---

## AI Webhook Integration (n8n)

**For chat, the AI response is fetched from an n8n webhook.**
- Set the `AI_WEBHOOK_URL` in your `.env` to your n8n webhook endpoint.
- The backend will POST `{ "session_id": ..., "human_message": ... }` to this URL and expects a JSON response with the AI's reply.

---

## Example .env
```
DATABASE_URL=postgresql://postgres:password@localhost/n8n_chatboat
SECRET_KEY=supersecretkey
AI_WEBHOOK_URL=https://your-n8n-instance/webhook/ai-chat
WEBHOOK_TIMEOUT=300
API_BASE_URL=http://localhost:8000
```

---

## License
MIT
