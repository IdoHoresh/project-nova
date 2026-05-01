from pathlib import Path

import lancedb
import pyarrow as pa


class VectorStore:
    """LanceDB-backed nearest-neighbor store for board embeddings."""

    TABLE = "memory_embeddings"
    DIM = 16  # must match nova_agent.llm.embeddings.EMBED_DIM

    def __init__(self, path: Path):
        from nova_agent.llm.embeddings import EMBED_DIM
        if EMBED_DIM != self.DIM:
            raise RuntimeError(
                f"VectorStore.DIM ({self.DIM}) != embeddings.EMBED_DIM ({EMBED_DIM}) — "
                f"update both in lockstep."
            )
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self._db = lancedb.connect(str(self.path))
        if self.TABLE not in self._db.table_names():
            schema = pa.schema(
                [
                    pa.field("id", pa.string()),
                    pa.field("vector", pa.list_(pa.float32(), self.DIM)),
                ]
            )
            self._db.create_table(self.TABLE, schema=schema)
        self._tbl = self._db.open_table(self.TABLE)

    def upsert(self, id: str, vector: list[float]) -> None:
        if len(vector) != self.DIM:
            raise ValueError(f"vector must have {self.DIM} dims; got {len(vector)}")
        self._tbl.delete(f"id = '{id}'")
        self._tbl.add([{"id": id, "vector": vector}])

    def search(self, vector: list[float], k: int = 5) -> list[tuple[str, float]]:
        results = self._tbl.search(vector).limit(k).to_list()
        return [(r["id"], float(r["_distance"])) for r in results]
