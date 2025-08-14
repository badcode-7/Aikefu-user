# retriever.py
import os, json, hnswlib, numpy as np
import sys
from typing import List, Tuple
from sentence_transformers import SentenceTransformer

def get_resource_path(relative_path):
    """获取打包后资源的绝对路径"""
    try:
        base_path = sys._MEIPASS  # PyInstaller创建的临时文件夹
    except AttributeError:
        base_path = os.path.abspath(".")  # 开发环境
    
    return os.path.join(base_path, relative_path)

class LocalRetriever:
    def __init__(self, model_dir: str, index_dir: str, dim: int = 768):
        self.model_dir = model_dir
        self.index_dir = index_dir
        os.makedirs(index_dir, exist_ok=True)
        self.dim = dim
        self.model = None
        self.index = None
        self.id2text = {}
        self._load_all()

    def _load_model(self):
        # 离线加载
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_DATASETS_OFFLINE"] = "1"
        self.model = SentenceTransformer(get_resource_path(self.model_dir))

    def _load_index(self):
        idx_path = os.path.join(get_resource_path(self.index_dir), "kb.index")
        map_path = os.path.join(get_resource_path(self.index_dir), "id2text.json")
        if os.path.exists(idx_path) and os.path.exists(map_path):
            with open(map_path, "r", encoding="utf-8") as f:
                self.id2text = json.load(f)
            p = hnswlib.Index(space="cosine", dim=self.dim)
            p.load_index(idx_path)
            self.index = p

    def _load_all(self):
        self._load_model()
        self._load_index()

    def build_from_texts(self, texts: List[str], ef_construction=200, M=16):
        # 编码
        embs = self.model.encode(texts, batch_size=32, normalize_embeddings=True)
        embs = np.array(embs, dtype=np.float32)
        # 建索引
        p = hnswlib.Index(space="cosine", dim=embs.shape[1])
        p.init_index(max_elements=len(texts), ef_construction=ef_construction, M=M)
        p.add_items(embs, ids=np.arange(len(texts)))
        p.set_ef(64)
        self.index = p
        # 保存映射
        self.id2text = {str(i): texts[i] for i in range(len(texts))}
        # 持久化
        p.save_index(os.path.join(get_resource_path(self.index_dir), "kb.index"))
        with open(os.path.join(get_resource_path(self.index_dir), "id2text.json"), "w", encoding="utf-8") as f:
            json.dump(self.id2text, f, ensure_ascii=False)

    def search(self, query: str, top_k=3) -> List[Tuple[str, float]]:
        if not self.index:
            return []
        q = self.model.encode([query], normalize_embeddings=True)
        labels, dists = self.index.knn_query(q, k=min(top_k, len(self.id2text)))
        res = []
        for i, score in zip(labels[0], dists[0]):
            res.append((self.id2text.get(str(i), ""), float(score)))
        return res
