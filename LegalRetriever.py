import lancedb
from legalbert_embedder import LegalBERTEmbedder
import pandas as pd

class LegalRetriever:
    def __init__(self, top_k: int = 5):
        self.model = LegalBERTEmbedder()
        self.top_k = top_k
        self.dbs = {}

    def _get_table(self, db_path: str, table_name: str):
        if db_path not in self.dbs:
            try:
                self.dbs[db_path] = lancedb.connect(db_path)
            except Exception as e:
                raise RuntimeError(f"Failed to connect to DB at {db_path}: {str(e)}")
        try:
            return self.dbs[db_path].open_table(table_name)
        except Exception as e:
            raise RuntimeError(f"Failed to open table '{table_name}' in DB '{db_path}': {str(e)}")

    def query_multiple(self, query_text: str, tables: list[dict]) -> list:
        try:
            query_vec = self.model.encode([query_text])[0].tolist()
        except Exception as e:
            raise RuntimeError(f"Failed to embed query: {str(e)}")

        all_results = []

        for tbl in tables:
            try:
                table = self._get_table(tbl["db_path"], tbl["table_name"])
                df = table.search(query_vec).limit(self.top_k).to_df()
                all_results.append(df)
            except Exception as e:
                print(f"Warning: Failed to query table '{tbl['table_name']}' in DB '{tbl['db_path']}': {str(e)}")

        if not all_results:
            return []

        try:
            merged_df = pd.concat(all_results, ignore_index=True)
            if "_distance" in merged_df.columns:
                merged_df = merged_df.sort_values(by="_distance", ascending=True)
        except Exception as e:
            raise RuntimeError(f"Failed to process merged results: {str(e)}")

        return [
            {
                "id": row.get("id"),
                "chunk": row.get("chunk"),
                "part_title": row.get("part_title"),
                "chapter_title": row.get("chapter_title"),
                "section_title": row.get("section_title"),
                "page": row.get("page"),
                "source": row.get("source"),
                "score": row.get("_distance")
            }
            for _, row in merged_df.iterrows()
        ][:self.top_k]