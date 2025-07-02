import streamlit as st
import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = []
if "messages" not in st.session_state:
    st.session_state.messages = []

# API helper functions
def make_request(method, endpoint, data=None, headers=None):
    """Make API request with error handling"""
    url = f"{API_BASE_URL}{endpoint}"
    default_headers = {"Content-Type": "application/json"}
    
    if headers:
        default_headers.update(headers)
    
    if st.session_state.access_token:
        default_headers["Authorization"] = f"Bearer {st.session_state.access_token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=default_headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=default_headers)
        
        if response.status_code == 401:
            st.session_state.access_token = None
            st.error("Session expired. Please login again.")
            st.rerun()
        
        return response
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None

def login_user(username, password):
    """Login user and get access token"""
    data = {"username": username, "password": password}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/login",
            data=data,
            headers=headers
        )
        
        if response.status_code == 200:
            token_data = response.json()
            st.session_state.access_token = token_data["access_token"]
            return True
        else:
            st.error("Invalid credentials")
            return False
    except requests.exceptions.RequestException as e:
        st.error(f"Login failed: {e}")
        return False

def register_user(email, username, full_name, password):
    """Register new user"""
    data = {
        "email": email,
        "username": username,
        "full_name": full_name,
        "password": password
    }
    
    response = make_request("POST", "/register", data)
    if response and response.status_code == 201:
        st.success("Registration successful! Please login.")
        return True
    else:
        error_msg = response.json().get("detail", "Registration failed") if response else "Registration failed"
        st.error(error_msg)
        return False

def get_user_info():
    """Get current user information"""
    response = make_request("GET", "/me")
    if response and response.status_code == 200:
        st.session_state.user_info = response.json()
        return True
    return False

def get_chat_sessions():
    """Get user's chat sessions"""
    response = make_request("GET", "/chat/sessions")
    if response and response.status_code == 200:
        st.session_state.chat_sessions = response.json()
        return True
    return False

def create_chat_session(session_name=None):
    """Create new chat session"""
    data = {"session_name": session_name}
    response = make_request("POST", "/chat/session", data)
    if response and response.status_code == 200:
        session = response.json()
        st.session_state.current_session_id = session["id"]
        get_chat_sessions()  # Refresh sessions list
        st.session_state.messages = []  # Clear current messages
        return True
    return False

def send_message(message):
    """Send chat message"""
    data = {
        "message": message,
        "session_id": st.session_state.current_session_id
    }
    response = make_request("POST", "/chat/message", data)
    if response and response.status_code == 200:
        return response.json()
    return None

def get_chat_history(session_id):
    """Get chat history for session"""
    response = make_request("GET", f"/chat/history/{session_id}")
    if response and response.status_code == 200:
        return response.json()
    return []

def logout():
    """Logout user"""
    make_request("POST", "/logout")
    st.session_state.access_token = None
    st.session_state.user_info = None
    st.session_state.current_session_id = None
    st.session_state.chat_sessions = []
    st.session_state.messages = []

# Authentication UI
def show_auth_page():
    """Show login/register page"""
    st.title("🤖 AI Chatbot")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Login")
            
            if submit_login and username and password:
                if login_user(username, password):
                    st.success("Login successful!")
                    st.rerun()
    
    with tab2:
        st.subheader("Register")
        with st.form("register_form"):
            email = st.text_input("Email")
            username = st.text_input("Username")
            full_name = st.text_input("Full Name")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit_register = st.form_submit_button("Register")
            
            if submit_register:
                if not all([email, username, password]):
                    st.error("Please fill all required fields")
                elif password != confirm_password:
                    st.error("Passwords don't match")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    register_user(email, username, full_name, password)

# Main chat interface
def show_chat_page():
    """Show main chat interface"""
    # Get user info if not already loaded
    if not st.session_state.user_info:
        get_user_info()
    
    # Sidebar
    with st.sidebar:
        st.title("🤖 AI Chatbot")
        
        if st.session_state.user_info:
            st.write(f"Welcome, {st.session_state.user_info['username']}!")
        
        st.markdown("---")
        
        # New chat button
        if st.button("➕ New Chat", use_container_width=True):
            create_chat_session()
            st.rerun()
        
        st.markdown("---")
        
        # Chat sessions
        st.subheader("Chat Sessions")
        get_chat_sessions()
        
        for session in st.session_state.chat_sessions:
            session_name = session["session_name"] or f"Session {session['id']}"
            if st.button(
                session_name, 
                key=f"session_{session['id']}",
                use_container_width=True
            ):
                st.session_state.current_session_id = session["id"]
                st.session_state.messages = get_chat_history(session["id"])
                st.rerun()
        
        st.markdown("---")
        
        # Logout button
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()
    
    # Main chat area
    st.title("💬 Chat")
    
    # Create initial session if none exists
    if not st.session_state.current_session_id and not st.session_state.chat_sessions:
        if create_chat_session("Welcome Chat"):
            st.rerun()
    
    # Display chat messages
    if st.session_state.current_session_id:
        # Load messages if not already loaded
        if not st.session_state.messages:
            st.session_state.messages = get_chat_history(st.session_state.current_session_id)
        
        # Display messages
        for msg in st.session_state.messages:
            with st.chat_message("user"):
                st.write(msg["message"])
            with st.chat_message("assistant"):
                st.write(msg["response"])
        
        # Chat input
        if prompt := st.chat_input("Type your message here..."):
            # Display user message
            with st.chat_message("user"):
                st.write(prompt)
            
            # Send message and get response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = send_message(prompt)
                    if response:
                        st.write(response["response"])
                        # Add to session state for immediate display
                        st.session_state.messages.append(response)
                    else:
                        st.error("Failed to get response. Please try again.")
    else:
        st.info("Create a new chat or select an existing session to start chatting!")

# Main app logic
def main():
    """Main application logic"""
    if st.session_state.access_token:
        show_chat_page()
    else:
        show_auth_page()

if __name__ == "__main__":
    main()