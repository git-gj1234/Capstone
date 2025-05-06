import os
import logging
from datetime import datetime
from models import LegalDocument, legal_documents, get_document_by_id

# Sample legal documents for initial population
SAMPLE_DOCUMENTS = [
    {
        'id': 'sec-10b-5',
        'title': 'SEC Rule 10b-5 - Employment of Manipulative and Deceptive Practices',
        'content': '''
It shall be unlawful for any person, directly or indirectly, by the use of any means or instrumentality of interstate commerce, or of the mails or of any facility of any national securities exchange,

(a) To employ any device, scheme, or artifice to defraud,
(b) To make any untrue statement of a material fact or to omit to state a material fact necessary in order to make the statements made, in the light of the circumstances under which they were made, not misleading, or
(c) To engage in any act, practice, or course of business which operates or would operate as a fraud or deceit upon any person, in connection with the purchase or sale of any security.
        ''',
        'document_type': 'regulation',
        'jurisdiction': 'United States',
        'publication_date': datetime.strptime('1942-05-21', '%Y-%m-%d').date(),
        'source': 'Securities and Exchange Commission'
    },
    {
        'id': 'dodd-frank-sec-1502',
        'title': 'Dodd-Frank Act Section 1502 - Conflict Minerals',
        'content': '''
(a) REGULATIONS.—
(1) IN GENERAL.—Not later than 270 days after the date of the enactment of this Act, the Commission shall promulgate regulations requiring any person described in paragraph (2) to disclose annually, beginning with the person's first full fiscal year that begins not less than 1 year after the date of promulgation of such regulations, whether conflict minerals that are necessary as described in paragraph (2)(B), in the year for which such reporting is required, did originate in the Democratic Republic of the Congo or an adjoining country and, in cases in which such conflict minerals did originate in any such country, submit to the Commission a report that includes, with respect to the period covered by the report—
(A) a description of the measures taken by the person to exercise due diligence on the source and chain of custody of such minerals, which measures shall include an independent private sector audit of such report submitted through the Commission that is conducted in accordance with standards established by the Comptroller General of the United States, in accordance with rules promulgated by the Commission, in consultation with the Secretary of State; and
(B) a description of the products manufactured or contracted to be manufactured that are not DRC conflict free ("DRC conflict free" is defined to mean the products that do not contain minerals that directly or indirectly finance or benefit armed groups in the Democratic Republic of the Congo or an adjoining country), the entity that conducted the independent private sector audit in accordance with subparagraph (A), the facilities used to process the conflict minerals, the country of origin of the conflict minerals, and the efforts to determine the mine or location of origin with the greatest possible specificity.
        ''',
        'document_type': 'statute',
        'jurisdiction': 'United States',
        'publication_date': datetime.strptime('2010-07-21', '%Y-%m-%d').date(),
        'source': 'Dodd-Frank Wall Street Reform and Consumer Protection Act'
    },
    {
        'id': 'basel-iii',
        'title': 'Basel III Framework',
        'content': '''
The Basel III Framework is a global regulatory standard on bank capital adequacy, stress testing, and market liquidity risk. It was developed in response to the deficiencies in financial regulation revealed by the financial crisis of 2007-08. Basel III strengthens bank capital requirements by increasing bank liquidity and decreasing bank leverage.

Basel III introduces new regulatory requirements on bank liquidity and bank leverage. Banks are required to hold 4.5% of common equity (up from 2% in Basel II) and 6% of Tier I capital (up from 4% in Basel II) of risk-weighted assets (RWA). Basel III also introduces additional capital buffers, (i) a mandatory capital conservation buffer of 2.5% and (ii) a discretionary countercyclical buffer, which allows national regulators to require up to another 2.5% of capital during periods of high credit growth.

In addition, Basel III introduces a minimum 3% leverage ratio and two required liquidity ratios. The Liquidity Coverage Ratio requires a bank to hold sufficient high-quality liquid assets to cover its total net cash outflows over 30 days; the Net Stable Funding Ratio requires the available amount of stable funding to exceed the required amount of stable funding over a one-year period of extended stress.
        ''',
        'document_type': 'standard',
        'jurisdiction': 'International',
        'publication_date': datetime.strptime('2010-12-16', '%Y-%m-%d').date(),
        'source': 'Basel Committee on Banking Supervision'
    },
    {
        'id': 'mifid-ii',
        'title': 'Markets in Financial Instruments Directive II (MiFID II)',
        'content': '''
MiFID II is a legislative framework instituted by the European Union (EU) to regulate financial markets in the bloc and improve protections for investors with the aim of restoring confidence in the industry after the 2008 financial crisis.

Key provisions of MiFID II include:

1. Increased transparency requirements for trading activities
2. Enhanced investor protection measures
3. Stricter rules on inducements and research
4. Trading venue regulations
5. Position limits for commodity derivatives
6. Requirements for algorithmic and high-frequency trading
7. Non-discriminatory access to clearing facilities
8. Enhanced powers for regulatory authorities

MiFID II requires investment firms to act honestly, fairly, and in the best interest of their clients. It prohibits firms from accepting and retaining fees, commissions, or any monetary or non-monetary benefits from third parties in relation to the provision of investment or ancillary services to clients, except for minor non-monetary benefits that are capable of enhancing the quality of service provided.
        ''',
        'document_type': 'directive',
        'jurisdiction': 'European Union',
        'publication_date': datetime.strptime('2014-05-15', '%Y-%m-%d').date(),
        'source': 'European Securities and Markets Authority (ESMA)'
    },
    {
        'id': 'sarbanes-oxley-sec-404',
        'title': 'Sarbanes-Oxley Act Section 404 - Management Assessment of Internal Controls',
        'content': '''
MANAGEMENT ASSESSMENT OF INTERNAL CONTROLS.—

(a) RULES REQUIRED.—The Commission shall prescribe rules requiring each annual report required by section 13(a) or 15(d) of the Securities Exchange Act of 1934 to contain an internal control report, which shall—
    (1) state the responsibility of management for establishing and maintaining an adequate internal control structure and procedures for financial reporting; and
    (2) contain an assessment, as of the end of the most recent fiscal year of the issuer, of the effectiveness of the internal control structure and procedures of the issuer for financial reporting.

(b) INTERNAL CONTROL EVALUATION AND REPORTING.—With respect to the internal control assessment required by subsection (a), each registered public accounting firm that prepares or issues the audit report for the issuer shall attest to, and report on, the assessment made by the management of the issuer. An attestation made under this subsection shall be made in accordance with standards for attestation engagements issued or adopted by the Board. Any such attestation shall not be the subject of a separate engagement.
        ''',
        'document_type': 'statute',
        'jurisdiction': 'United States',
        'publication_date': datetime.strptime('2002-07-30', '%Y-%m-%d').date(),
        'source': 'Sarbanes-Oxley Act'
    }
]

def initialize_documents():
    """Initialize the in-memory list with sample documents if empty"""
    global legal_documents
    
    if not legal_documents:
        logging.info("Initializing legal documents with sample data")
        for doc_data in SAMPLE_DOCUMENTS:
            doc = LegalDocument(**doc_data)
            legal_documents.append(doc)
        logging.info(f"Added {len(SAMPLE_DOCUMENTS)} sample documents to memory")

def get_legal_references(reference_data):
    """
    Get legal references based on document IDs with relevance scores
    
    Args:
        reference_data (list): List of document IDs with relevance scores and excerpts
            Each item should be a dict with at least 'id' key and optionally 'relevance' and 'excerpt' keys
        
    Returns:
        list: List of document references
    """
    references = []
    
    for ref in reference_data:
        # Handle both old format (just ID string) and new format (dict with id and relevance)
        if isinstance(ref, str):
            doc_id = ref
            relevance = 100
            excerpt = None
        else:
            doc_id = ref.get('id')
            relevance = ref.get('relevance', 100)
            excerpt = ref.get('excerpt')
            
        doc = get_document_by_id(doc_id)
        if doc:
            # Use provided excerpt or create a preview from content
            if excerpt:
                content_preview = excerpt
            else:
                content_preview = doc.content.strip()[:200] + "..." if len(doc.content) > 200 else doc.content
                
            references.append({
                'id': doc.id,
                'title': doc.title,
                'content_preview': content_preview,
                'document_type': doc.document_type,
                'source': doc.source,
                'relevance': relevance
            })
            
    # Sort references by relevance score (highest first)
    references.sort(key=lambda x: x.get('relevance', 0), reverse=True)
    print("from legal_docs.get legal refs")
    print(references)
    return references

def get_document_text(doc_id):
    """
    Get the full text of a document
    
    Args:
        doc_id (str): Document ID
        
    Returns:
        dict: Document data
    """
    doc = get_document_by_id(doc_id)
    if doc:
        return doc.to_dict()
    return None

def search_documents(query):
    """
    Search for documents by keyword
    
    Args:
        query (str): Search query
        
    Returns:
        list: List of matching documents
    """
    # Simple search implementation - in a real app, use a proper search engine
    results = []
    search_term = query.lower()
    
    for doc in legal_documents:
        if (search_term in doc.title.lower() or 
            search_term in doc.content.lower()):
            
            # Create a preview of the content
            content_preview = doc.content.strip()[:200] + "..." if len(doc.content) > 200 else doc.content
            
            results.append({
                'id': doc.id,
                'title': doc.title,
                'content_preview': content_preview,
                'document_type': doc.document_type,
                'source': doc.source
            })
    
    return results
