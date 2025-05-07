import os
import json
import logging
from LegalRetriever import LegalRetriever
import google.generativeai as genai
from typing import List, Dict
import lancedb
from company_docs_retreiver import relevant_refs_from_query

# 🔧 CONFIGURATION
config = {
    "model_name": "nlpaueb/legal-bert-base-uncased",
    "comp_pdf": "CompaniesAct.pdf",
    "bank_pdf": "BankruptcyAct.pdf",
    "db_path": "./Data",
    # Table names for LanceDB
    "comp_table": "CompaniesAct",
    "bank_table": "BankruptcyAct",
    "constitution_table": "IndianConstitution",
    # CSV path for Indian Constitution
    "constitution_csv": "Indian_Constitution.csv"
}
# Initialize Google Gemini AI
GEMINI_API_KEY = "AIzaSyBZym64q7Mhw_atOCA4qUX3MMTLEMeY5Tk"
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Import legal document functions
from legal_docs import get_document_text
from models import legal_documents, LegalDocument

def get_chat_response(user_message):
    """
    Get a response from the Gemini AI chatbot for a financial legal question
    
    Args:
        user_message (str): The user's message
        
    Returns:
        tuple: (response_text, list_of_reference_ids_with_scores)
    """
    # Log the start of the function and the user message
    logging.info(f"Starting chat response generation for: {user_message[:50]}...")
    logging.info(f"Gemini API key set @{GEMINI_API_KEY[:10]}...")
    if not GEMINI_API_KEY:
        logging.error("GEMINI_API_KEY not set in environment variables")
        return "I'm sorry, but I can't respond at the moment due to configuration issues. Please make sure the GEMINI_API_KEY is properly set in your environment.", []
    remap = {"Companies Act":"CompaniesAct", "Bankruptcy Act": "BankruptcyAct"}
    try:
        global legal_documents
        # Get all document IDs for context (from in-memory storage)
        logging.info(f"Preparing document summaries from {len(legal_documents)} documents")
        doc_summaries = []
        #RAG LOGIC
        retriever = LegalRetriever(top_k=3)
        retriever = LegalRetriever(top_k=5)
        def query_legal_documents(query: str) -> List[Dict]:
            tables = [
                {"db_path": config["db_path"], "table_name": config["comp_table"]},
                {"db_path": config["db_path"], "table_name": config["bank_table"]},
                {"db_path": config["db_path"], "table_name": config["constitution_table"]}
            ]
            return retriever.query_multiple(query, tables)
        legal_documents = []
        legal_documents_unformatted = query_legal_documents(query=str(user_message))
        for le_do in legal_documents_unformatted:
            doc_object = {
            'id': le_do["id"],
            'title': str(le_do["score"]) + " " + str(le_do["chapter_title"])+ " " + str(le_do["section_title"]),
            'content': le_do["chunk"],
            'document_type': "law",
            'source': le_do["source"]
            }
            legal_documents.append(LegalDocument(**doc_object))
        
        #END OF RAG LOGIC
        print(legal_documents)
        for doc in legal_documents:
            doc_summaries.append({
                "id": doc.id,
                "title": doc.title,
                "type": remap[doc.source],
                "summary": doc.content
            })
        for doc in legal_documents:
            print(doc.content)
        
        # Create the prompt with system instructions and context
        logging.info("Creating prompt for Gemini AI")
        prompt = f"""
You are a financial legal assistant specializing in financial regulations and laws. 
Your task is to provide accurate information about financial legal matters.

For each response, you must:
1. Provide a clear, accurate answer based on actual financial laws and regulations
2. Cite specific legal documents that support your answer
3. Format your response in JSON with the following sections:
   - "answer": Your detailed response to the user's question
   - "references": A list of objects containing:
     - "id": The document ID from the provided context
     - "relevance": A score from 0-100 (string) indicating how relevant this document is to the question
     - "excerpt": A brief excerpt from the document that specifically supports your answer

Include ALL potentially relevant documents in your references list with their relevance scores.
Sort references by relevance score (highest first). In case of no relevance, add 3 references presented.

Be concise but thorough. Focus on factual legal information rather than opinions.

Question: {user_message}

Available legal document context:
{json.dumps(doc_summaries, indent=2)}

Please analyze the question and provide an accurate response with properly scored legal references.
Format your response as JSON with the keys described above.
"""
        words = ["my", "system", "changes", "change"]
        if any(word in user_message for word in words):
            results = relevant_refs_from_query(user_message)
            prompt = f"""
You are a financial legal assistant specializing in financial regulations and laws. 
Your task is to provide accurate information about financial legal matters.
You will be provided with a set of possibly relevant legal clauses from the internal agreements of the organisation. 
Given the user query, for every relevant piece of input,
output necessary information or changes as requested by the user
For each response, you must:
1. Provide a clear, accurate answer based on actual financial laws and regulations
Include ALL potentially relevant documents in your references list with their relevance scores.
Be concise but thorough. Focus on factual legal information rather than opinions.

Question: {user_message}

Available legal document context:
{json.dumps(results, indent=2)}

Please analyze the question and provide an accurate response with properly strcutured outputs clearly explaining
"""
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return response.text, results

        # Call Gemini API
        logging.info("Calling Gemini API with gemini-1.5-flash model")
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        
        # Parse the response
        logging.info("Received response from Gemini API, parsing content")
        response_content = response.text
        
        # Try to extract JSON from the response
        try:
            # First try direct parsing
            logging.info("Attempting to parse response as JSON")
            response_data = json.loads(response_content)
            logging.info("Successfully parsed JSON directly")
        except json.JSONDecodeError as e:
            logging.warning(f"Failed direct JSON parsing: {str(e)}")
            # If that fails, try to find JSON within markdown code blocks
            import re
            logging.info("Attempting to extract JSON from code blocks")
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_content)
            if json_match:
                try:
                    response_data = json.loads(json_match.group(1))
                    logging.info("Successfully extracted and parsed JSON from code block")
                except json.JSONDecodeError as e:
                    logging.error(f"Failed to parse JSON from code block: {str(e)}")
                    # If still failing, create a simple structure
                    response_data = {
                        "answer": response_content,
                        "references": []
                    }
                    logging.info("Using fallback structure with full response as answer")
            else:
                logging.warning("No JSON code blocks found, using default structure")
                # Default fallback
                response_data = {
                    "answer": response_content,
                    "references": []
                }
        
        # Extract answer and references
        answer = response_data.get("answer", "I couldn't find specific information about that topic.")
        references = response_data.get("references", [])
        logging.info(f"Extracted answer (length: {len(answer)}) and {len(references)} references")
        
        # Extract just the IDs if references are in the new format
        reference_data = []
        if references and isinstance(references, list):
            if len(references) > 0 and isinstance(references[0], dict) and "id" in references[0]:
                # New format with relevance scores
                reference_data = references
                logging.info("Found references in new format with relevance scores")
            else:
                # Old format with just IDs
                reference_data = [{"id": ref_id, "relevance": 100} for ref_id in references]
                logging.info("Found references in old format, converted to new format")
        x = []
        for r in references:
            x.append(next((d for d in legal_documents_unformatted if d.get("id") == r["id"]), None)
)
        logging.info("Successfully generated response")
        print(answer)
        print(x)
        return answer, x
        
    except Exception as e:
        logging.error(f"Error getting chat response: {str(e)}", exc_info=True)
        error_message = (
            f"I apologize, but I encountered an error while processing your request: {str(e)}. "
            "This might be due to API key issues or network connectivity problems. "
            "Please check your GEMINI_API_KEY environment variable and internet connection."
        )
        return error_message, []
