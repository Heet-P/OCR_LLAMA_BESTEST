from app.db.supabase import supabase
from app.core.llm.gemini_client import gemini_client
import uuid
from typing import Dict, Any, List, Optional

class ChatService:
    def __init__(self):
        self.llm = gemini_client

    async def create_session(self, form_id: str) -> Dict[str, Any]:
        """
        Initialize a new chat session for a form.
        """
        # Fetch form schema
        form = supabase.table("forms").select("form_schema").eq("id", form_id).single().execute()
        if not form.data:
            raise ValueError("Form not found or has no schema")
            
        schema = form.data['form_schema']
        if not schema or 'fields' not in schema or not schema['fields']:
             raise ValueError("Form schema is invalid or empty")
             
        first_field = schema['fields'][0]
        
        # Create session
        session_data = {
            "form_id": form_id,
            "status": "active",
            "current_field_id": first_field['id'],
            "form_data": {}
        }
        
        res = supabase.table("sessions").insert(session_data).execute()
        session = res.data[0]
        
        # Initial greeting is the first question
        await self._save_message(session['id'], "assistant", first_field['question'])
        
        return {
            "session_id": session['id'],
            "message": first_field['question'],
            "field": first_field
        }

    async def _save_message(self, session_id: str, role: str, content: str):
        supabase.table("messages").insert({
            "session_id": session_id,
            "role": role,
            "content": content
        }).execute()

    async def process_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """
        Process user input, validate it, update state, and return next response.
        """
        # Get session state
        session_res = supabase.table("sessions").select("*").eq("id", session_id).single().execute()
        if not session_res.data:
            raise ValueError("Session not found")
        session = session_res.data
        
        # Get form schema
        form_res = supabase.table("forms").select("form_schema").eq("id", session['form_id']).single().execute()
        schema = form_res.data['form_schema']
        fields = {f['id']: f for f in schema['fields']}
        field_ids = [f['id'] for f in schema['fields']]
        
        current_field_id = session['current_field_id']
        current_field = fields.get(current_field_id)
        
        # Save user message
        await self._save_message(session_id, "user", user_message)

        # 1. Validate Answer (using Gemini or simple rules)
        # For MVP, we'll try to infer if it's a valid answer using LLM
        validation_prompt = f"""
        Field: {current_field['label']}
        Type: {current_field['type']}
        Question: {current_field['question']}
        User Answer: {user_message}
        
        Is this a valid answer? If yes, extract the clean value. If no, provide varied feedback.
        Return JSON: {{"valid": boolean, "value": any, "feedback": "string"}}
        """
        
        # Using a specialized prompt to Gemini
        llm_response = await self.llm.generate_content(validation_prompt)
        try:
            # Simple cleanup for JSON parsing
            clean_json = llm_response.replace("```json", "").replace("```", "").strip()
            import json
            validation = json.loads(clean_json)
        except:
            # Fallback if LLM fails
            validation = {"valid": True, "value": user_message}

        if not validation.get("valid", False):
            # Ask again with feedback
            feedback = validation.get("feedback", "I didn't understand that. Could you please check your answer?")
            await self._save_message(session_id, "assistant", feedback)
            return {"message": feedback, "status": "retry"}

        # 2. Update Form Data
        current_data = session['form_data'] or {}
        current_data[current_field_id] = validation.get("value", user_message)
        
        # 3. Move to next field
        try:
            curr_idx = field_ids.index(current_field_id)
            if curr_idx + 1 < len(field_ids):
                next_field_id = field_ids[curr_idx + 1]
                next_field = fields[next_field_id]
                next_question = next_field['question']
                next_status = "active"
            else:
                next_field_id = None
                next_question = "Great! You've completed the form."
                next_status = "completed"
                
            # Update Session
            supabase.table("sessions").update({
                "form_data": current_data,
                "current_field_id": next_field_id,
                "status": next_status
            }).eq("id", session_id).execute()
            
            # Save Assistant Message
            await self._save_message(session_id, "assistant", next_question)
            
            return {
                "message": next_question,
                "status": next_status,
                "completed": next_status == "completed",
                "field_label": next_field['label'] if next_field_id else None
            }
            
        except ValueError:
             return {"message": "Error in form flow", "status": "error"}

chat_service = ChatService()
