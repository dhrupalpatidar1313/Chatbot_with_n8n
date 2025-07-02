from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
import asyncio
import uuid
from app.database import get_db, engine
from app.models import Base, User, ChatSession, ChatMessage
from app.schemas import (
    UserCreate, UserResponse, Token, MessageResponse,
    ChatMessageCreate, ChatMessageResponse, ChatSessionCreate, ChatSessionResponse
)
from app.auth import (
    authenticate_user, 
    create_access_token, 
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    blacklist_token,
    oauth2_scheme
)
from app.ai_service import ai_service
import app.crud as crud

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="FastAPI Authentication System",
    description="A complete authentication system with login/logout functionality",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to FastAPI Authentication System"}

@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    
    # Check if user already exists by email
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Check if user already exists by username
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )
    
    # Create new user
    return crud.create_user(db=db, user=user)

@app.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login endpoint to get access token"""
    
    # Authenticate user
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer"
    }

@app.post("/logout", response_model=MessageResponse)
async def logout(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Logout endpoint to blacklist current token"""
    
    # Add token to blacklist
    blacklist_token(db, token)
    
    return {"message": "Successfully logged out"}

@app.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user

@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_active_user)):
    """Example protected route"""
    return {
        "message": f"Hello {current_user.username}, this is a protected route!",
        "user_id": current_user.id,
        "email": current_user.email
    }

# Chat Endpoints
@app.post("/chat/session", response_model=ChatSessionResponse)
async def create_chat_session(
    session: ChatSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session"""
    db_session = ChatSession(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        session_name=session.session_name or f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@app.get("/chat/sessions", response_model=list[ChatSessionResponse])
async def get_chat_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all chat sessions for current user"""
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).all()
    return sessions

@app.post("/chat/message", response_model=ChatMessageResponse)
async def send_chat_message(
    chat_request: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a chat message and get AI response"""
    
    # Create session if not provided
    session_id = chat_request.session_id
    if not session_id:
        new_session = ChatSession(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            session_name=f"Chat {datetime.now().strftime('%H:%M')}"
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        session_id = new_session.id
    
    # Validate session belongs to user
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Chat session not found"
        )
    
    # Get AI response from webhook
    ai_response = await ai_service.get_ai_response(session_id=str(session_id), human_msg=chat_request.message)
    
    if not ai_response:
        raise HTTPException(
            status_code=500,
            detail="Failed to get AI response"
        )
    
    # Save to database
    db_message = ChatMessage(
        session_id=session_id,
        user_id=current_user.id,
        message=chat_request.message,
        response=ai_response
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    return db_message

@app.get("/chat/history/{session_id}", response_model=list[ChatMessageResponse])
async def get_chat_history(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get chat history for a specific session"""
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id,
        ChatMessage.user_id == current_user.id
    ).order_by(ChatMessage.timestamp).all()
    
    return messages

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8000)