import lancedb
from legalbert_embedder import LegalBERTEmbedder
import pandas as pd

class LegalRetriever:
    def __init__(self, main_embedder_instance, top_k: int = 5):
        self.model = main_embedder_instance # Use the same embedder instance used for indexing
        self.top_k = top_k
        self.dbs = {}

    def _get_table(self, db_path: str, table_name: str):
        db_key = f"{db_path}_{table_name}" # Unique key for db connection + table
        if db_key not in self.dbs:
            try:
                db_conn = lancedb.connect(db_path)
                self.dbs[db_key] = db_conn.open_table(table_name)
            except Exception as e:
                raise RuntimeError(f"Failed to connect to DB at {db_path} or open table {table_name}: {str(e)}")
        return self.dbs[db_key]

    def query_multiple(self, query_text: str, tables_to_search: list[dict]) -> list:
        try:
            query_vec = self.model.encode([query_text])[0].tolist()
        except Exception as e:
            raise RuntimeError(f"Failed to embed query: {str(e)}")

        all_results_dfs = []

        for tbl_info in tables_to_search:
            try:
                table_obj = self._get_table(tbl_info["db_path"], tbl_info["table_name"])
                df = table_obj.search(query_vec).limit(self.top_k).to_pandas()
                all_results_dfs.append(df)
            except Exception as e:
                print(f"Warning: Failed to query table '{tbl_info['table_name']}' in DB '{tbl_info['db_path']}': {str(e)}")
        
        if not all_results_dfs:
            return []

        try:
            merged_df = pd.concat(all_results_dfs, ignore_index=True)
            if "_distance" in merged_df.columns:
                merged_df = merged_df.sort_values(by="_distance", ascending=True)
            else:
                 print("Warning: '_distance' column not found in search results for sorting.")
        except Exception as e:
            # If concat fails (e.g. empty list of dfs), return empty list or handle
            if not all_results_dfs:
                return []
            raise RuntimeError(f"Failed to process merged results: {str(e)}")
        
        # Format results
        output_results = []
        for _, row in merged_df.head(self.top_k).iterrows(): # Ensure only top_k overall are returned
            output_results.append({
                "id": row.get("id"),
                "chunk": row.get("chunk"),
                "part_title": row.get("part_title"),
                "chapter_title": row.get("chapter_title"),
                "section_title": row.get("section_title"),
                "page": row.get("page"),
                "source": row.get("source"),
                "score": row.get("_distance")
            })
        return output_results