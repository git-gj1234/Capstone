import os
import sys
import logging
import traceback
import math
from flask import Flask, render_template, request, jsonify, session
ads = []
# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Check for required environment variables
gemini_api_key = os.environ.get("GEMINI_API_KEY")
if not gemini_api_key:
    logging.warning("GEMINI_API_KEY environment variable is not set. Chatbot functionality will be limited.")
    print("\n" + "*" * 80)
    print("WARNING: GEMINI_API_KEY not set")
    print("For full functionality, please set the GEMINI_API_KEY environment variable.")
    print("*" * 80 + "\n")

# Import routes after app is created to avoid circular imports
from chatbot import get_chat_response
from legal_docs import get_legal_references, get_document_text, search_documents

@app.route('/')
def index():
    # Initialize chat history if it doesn't exist
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    return render_template('index.html', chat_history=session['chat_history'])

@app.route('/chat', methods=['POST'])
def chat():
    global ads
    logging.info("Chat endpoint called")
    user_message = request.form.get('message', '')
    logging.info(f"Received message: {user_message[:50]}...")
    
    if not user_message.strip():
        logging.warning("Empty message received")
        return jsonify({'error': 'Please enter a message'}), 400
    
    if not os.environ.get("GEMINI_API_KEY"):
        error_msg = "GEMINI_API_KEY not set. Please set this environment variable to use the chatbot."
        logging.error(error_msg)
        return jsonify({
            'error': error_msg,
            'help': "When running locally, make sure to set the GEMINI_API_KEY environment variable"
        }), 500
    
    try:
        logging.info(f"Processing message of length {len(user_message)}")
        # Get response from chatbot
        bot_response, reference_ids = get_chat_response(user_message)
        logging.info(f"Got response from chatbot (length: {len(bot_response)})")
        
        # Get legal references based on the response
        logging.info(f"Getting legal references for {len(reference_ids)} documents")
        # references = get_legal_references(reference_ids)
        # references = reference_ids
        references = [
            {
                "content_preview": ref["chunk"][:300] if len(ref["chunk"])>300 else ref["chunk"],
                "title": " ".join(
                    part for part in [ref.get("part_title"), ref.get("chapter_title"), ref.get("section_title")]
                    if part and str(part).lower() != "nan"
                ).strip(),
                "document_type":"Law",
                "source": ref["source"],
                "score":ref["score"],
                "id":ref["id"],
                "content":ref["chunk"]
            }
            for ref in reference_ids
        ]
        print
        print(references[0].keys())
        def sanitize_dict(d):
            return {
                k: (None if isinstance(v, float) and math.isnan(v) else v)
                for k, v in d.items()
            }

        references = [sanitize_dict(d) for d in references]
        ads = references
        logging.info(f"Got {len(references)} legal references")
        
        # Add to session history
        if 'chat_history' not in session:
            session['chat_history'] = []
            
        session['chat_history'].append({
            'user_message': user_message,
            'bot_response': bot_response,
            'references': references
        })
        
        # Limit history to last 10 conversations
        if len(session['chat_history']) > 10:
            session['chat_history'] = session['chat_history'][-10:]
            
        session.modified = True
        
        logging.info("Successfully processed chat request, returning response")
        return jsonify({
            'response': bot_response,
            'references': references
        })
    
    except Exception as e:
        error_traceback = traceback.format_exc()
        logging.error(f"Error in chat endpoint: {str(e)}")
        logging.error(f"Traceback: {error_traceback}")
        
        error_message = str(e)
        if "GEMINI_API_KEY" in error_message:
            error_message = "API key error. Please check that your GEMINI_API_KEY is valid."
        
        return jsonify({
            'error': f'An error occurred: {error_message}',
            'detail': 'Check the server logs for more information.'
        }), 500

@app.route('/document/<doc_id>')
def get_document(doc_id):
    global ads
    logging.info(f"Document request for ID: {doc_id}")
    try:
        # document = get_document_text(doc_id)
        document = next((d for d in ads if d.get("id") == doc_id), None)
        if document:
            logging.info(f"Found document with title: {document.get('title', 'Unknown')}")
            return jsonify(document)
        
        logging.warning(f"Document not found with ID: {doc_id}")
        return jsonify({
            'error': 'Document not found',
            'detail': f"No document found with ID: {doc_id}"
        }), 404
    except Exception as e:
        error_traceback = traceback.format_exc()
        logging.error(f"Error retrieving document: {str(e)}")
        logging.error(f"Traceback: {error_traceback}")
        return jsonify({
            'error': f'An error occurred retrieving the document: {str(e)}',
            'detail': 'Check the server logs for more information'
        }), 500

@app.route('/search', methods=['POST'])
def search():
    logging.info("Search endpoint called")
    query = request.form.get('query', '')
    logging.info(f"Search query: {query}")
    
    if not query.strip():
        logging.warning("Empty search query received")
        return jsonify({'error': 'Please enter a search query'}), 400
    
    try:
        logging.info(f"Searching for: {query}")
        results = search_documents(query)
        logging.info(f"Found {len(results)} results")
        return jsonify({'results': results})
    except Exception as e:
        error_traceback = traceback.format_exc()
        logging.error(f"Error in search endpoint: {str(e)}")
        logging.error(f"Traceback: {error_traceback}")
        return jsonify({
            'error': f'An error occurred during search: {str(e)}',
            'detail': 'Check the server logs for more information'
        }), 500

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    session['chat_history'] = []
    session.modified = True
    return jsonify({'status': 'success'})

# Initialize documents
from legal_docs import initialize_documents
initialize_documents()
