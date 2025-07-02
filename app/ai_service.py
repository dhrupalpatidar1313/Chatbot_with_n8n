import requests
import os
from dotenv import load_dotenv
from typing import Optional
import logging

load_dotenv()

# Configuration
AI_WEBHOOK_URL = os.getenv("AI_WEBHOOK_URL", "https://dummy-ai-webhook.example.com/chat")
WEBHOOK_TIMEOUT = int(os.getenv("WEBHOOK_TIMEOUT", "300"))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.webhook_url = AI_WEBHOOK_URL
        self.timeout = WEBHOOK_TIMEOUT

    async def get_ai_response(self , session_id: str, human_msg: str) -> Optional[str]:
        """
        Call AI webhook to get response
        
        Args:
            session_id: Chat session ID
            human_msg: Human message
            
        Returns:
            AI response string or None if failed
        """
        try:
            # Prepare webhook payload
            payload = {
                "session_id": str(session_id),
                "human_message": human_msg
            }
            
            # Headers
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "FastAPI-Chatbot/1.0"
            }
            
            logger.info(f"Calling AI webhook for session {session_id}")
            logger.debug(f"Payload: {payload}")
            
            # Make webhook request
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            # Check response status
            if response.status_code == 200:
                response_data = response.json()
                
                # Extract AI response from different possible response formats
                ai_response = self._extract_ai_response(response_data)
                
                if ai_response:
                    logger.info(f"Successfully got AI response for session {session_id}")
                    return ai_response
                else:
                    logger.error(f"No AI response found in webhook response: {response_data}")
                    return self._get_fallback_response("No response from AI")
            
            else:
                logger.error(f"Webhook failed with status {response.status_code}: {response.text}")
                return self._get_fallback_response(f"AI service error (Status: {response.status_code})")
        
        except requests.exceptions.Timeout:
            logger.error(f"Webhook timeout after {self.timeout} seconds")
            return self._get_fallback_response("AI service is taking too long to respond")
        
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to AI webhook")
            return self._get_fallback_response("AI service is currently unavailable")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Webhook request failed: {str(e)}")
            return self._get_fallback_response("AI service error")
        
        except Exception as e:
            logger.error(f"Unexpected error calling AI webhook: {str(e)}")
            return self._get_fallback_response("Unexpected error occurred")
    
    def _extract_ai_response(self, response_data: dict) -> Optional[str]:
        """
        Extract AI response from webhook response data
        Handles different possible response formats
        """
        # If response is a list, get the first item
        if isinstance(response_data, list) and response_data:
            response_data = response_data[0]
        
        # If response is a dict, check for 'output' key
        if isinstance(response_data, dict):
            if "output" in response_data and isinstance(response_data["output"], dict):
                # Now check for 'ai_response' in the output dict
                if "ai_response" in response_data["output"]:
                    return str(response_data["output"]["ai_response"])
            # Fallback to previous logic for other possible fields
            possible_fields = [
                "ai_response", "response", "message", "answer", "reply", "text", "content"
            ]
            for field in possible_fields:
                if field in response_data and response_data[field]:
                    return str(response_data[field])
        # If response is a string directly
        if isinstance(response_data, str):
            return response_data
        return None
    
    def _get_fallback_response(self, error_context: str) -> str:
        """
        Generate fallback response when AI webhook fails
        """
        fallback_responses = [
            "I'm sorry, I'm having trouble processing your request right now. Please try again in a moment.",
            "It seems there's a temporary issue with my AI service. Could you please rephrase your question?",
            "I'm experiencing some technical difficulties. Please try again shortly.",
            "Sorry, I couldn't process that right now. Let me know if you'd like to try again."
        ]
        
        # You can customize this logic based on error_context
        return fallback_responses[0]
    
    def test_webhook_connection(self) -> dict:
        """
        Test webhook connectivity
        Returns status information
        """
        try:
            test_payload = {
                "session_id": "0",
                "human_msg": "test connection"
            }
            
            response = requests.post(
                self.webhook_url,
                json=test_payload,
                timeout=5
            )
            
            return {
                "status": "success" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "webhook_url": self.webhook_url,
                "response_time": response.elapsed.total_seconds()
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "webhook_url": self.webhook_url
            }

# Create singleton instance
ai_service = AIService()