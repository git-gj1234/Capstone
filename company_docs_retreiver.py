import pandas as pd
from typing import List
import json
from lancedb.pydantic import LanceModel, Vector
import lancedb
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.embeddings import Embeddings
import ast
import lancedb
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.embeddings import Embeddings
import subprocess
from neo4j import GraphDatabase

# === Configuration ===
DB_PATH = "./Data"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "12345678"
GEMINI_API_KEY = "AIzaSyDxSbsQYWF1usd_31b8ujowFknAsu43SYQ"
genai.configure(api_key=GEMINI_API_KEY)

embeddings_model: Embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    task_type="RETRIEVAL_QUERY",
    google_api_key=GEMINI_API_KEY,
)

# === Connect to LanceDB ===
db = lancedb.connect(DB_PATH)
company_table = db.open_table("company_docs")


def get_embeddings(text: str) -> List[float]:
    return embeddings_model.embed_documents([text])[0]


def query_clause(query: str, k: int = 3):
    embedding = get_embeddings(query)
    # print(f"\n🔍 Top {k} clause matching:\n➡️ {query}\n")

    # build the query, then execute with .to_list()
    builder = (
        company_table
        .search(embedding, vector_column_name="chunk_embedding")
        .limit(k)
    )
    results = builder.to_list()   # ← here we actually run the search :contentReference[oaicite:0]{index=0}
    uids = []
    for i, row in enumerate(results, start=1):
        # print(row.keys())
        # print(f"{i}. uuid: {row['uid']} title: {row['doc_title']} , chunk: {row['doc_chunk']}")
        uids.append(row['uid'])
    return uids, results

def uid_llm_filter(query, dicts):
    prompt = f"""
you are a professional legal assistant. given a user query and a list of internal company document clauses, return those documents uids whose content mathces the query or may have implacation
for or from it. In case no exact mathces return uid for closest match. Return a list of the uids directly.
user query  : {query}
docs: {json.dumps(dicts)}
"""
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return ast.literal_eval(response.text)

def js_driver(uids):
    args = ["node", "modified_neo4j_driver.js"] + uids
    subprocess.Popen(args)

def get_linked_clauses(uids, results):
    QUERY = """
    MATCH (target {uid: $uid})
    OPTIONAL MATCH pathUp = (root)-[:INFLUENCES*]->(target)
    WITH CASE 
            WHEN pathUp IS NULL THEN target
            ELSE head(nodes(pathUp))
         END AS root
    MATCH tree = (root)-[:INFLUENCES*0..]->(descendants)
    RETURN root.uid AS root_uid, tree
    """
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    collected = []
    seen_uids = set()
    root_uids = set()

    for uid in uids:
        with driver.session() as session:
            result = session.run(QUERY, uid=uid)
            for record in result:
                root_uid = record["root_uid"]
                root_uids.add(root_uid)
                tree_path = record["tree"]
                for node in tree_path.nodes:
                    node_uid = node.get("uid")
                    if node_uid not in seen_uids:
                        seen_uids.add(node_uid)
                        collected.append({
                            "uid": node_uid,
                            "id": node_uid,
                            "title": str(node.get("title")) + " Section " + str(node.get("sn")) + " clause " + str(node.get("cn")),
                            "content_preview": node.get("chunk")[:100] if node.get("chunk") and len(node.get("chunk")) > 100 else node.get("chunk"),
                            "content": node.get("chunk"),
                            "document_type": "Internal Agreement",
                            "source": str(node.get("title")),
                            "score": next((d['_distance'] for d in results if d.get('uid') == node_uid), 0.74),
                            "chunk": node.get("chunk")
                        })

    return list(root_uids), collected

def relevant_refs_from_query(query):
    uids, results = query_clause(query)
    uids = uid_llm_filter(query, results)
    uids, results = get_linked_clauses(uids, results)
    js_driver(uids)
    return results