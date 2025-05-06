from datetime import datetime

class LegalDocument:
    """Class for legal documents stored in memory"""
    def __init__(self, id, title, content, document_type, jurisdiction=None, publication_date=None, source=None):
        self.id = id
        self.title = title
        self.content = content
        self.document_type = document_type
        self.jurisdiction = jurisdiction
        self.publication_date = publication_date
        self.source = source
        self.created_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'document_type': self.document_type,
            'jurisdiction': self.jurisdiction,
            'publication_date': self.publication_date.isoformat() if self.publication_date else None,
            'source': self.source
        }

class MessageReference:
    """Class for storing references between messages and legal documents"""
    def __init__(self, document_id, relevance_score=None, excerpt=None):
        self.document_id = document_id
        self.relevance_score = relevance_score
        self.excerpt = excerpt

class ChatMessage:
    """Class for storing chat messages"""
    def __init__(self, message, is_user=True):
        self.message = message
        self.is_user = is_user
        self.timestamp = datetime.utcnow()
        self.references = []

class ChatSession:
    """Class for storing chat sessions"""
    def __init__(self, session_id):
        self.session_id = session_id
        self.created_at = datetime.utcnow()
        self.messages = []

# In-memory storage
legal_documents = []
chat_sessions = []
current_session = None

def get_document_by_id(document_id):
    """Get a document by its ID"""
    for document in legal_documents:
        if document.id == document_id:
            return document
    return None

def get_or_create_session(session_id='default'):
    """Get or create a chat session"""
    global current_session
    
    # Check if session exists
    for session in chat_sessions:
        if session.session_id == session_id:
            current_session = session
            return session
    
    # Create new session
    new_session = ChatSession(session_id)
    chat_sessions.append(new_session)
    current_session = new_session
    return new_session

def clear_current_session():
    """Clear the current session"""
    global current_session
    
    if current_session:
        # Find and remove the current session
        for i, session in enumerate(chat_sessions):
            if session.session_id == current_session.session_id:
                chat_sessions.pop(i)
                break
        
        # Create a new session with the same ID
        current_session = ChatSession(current_session.session_id)
        chat_sessions.append(current_session)
        return True
    
    return False
