# retriever.py
import os, json, sys
from typing import List, Tuple
import sys, os
if getattr(sys, "frozen", False):
    base = os.path.dirname(sys.executable)
    internal = os.path.join(base, "_internal")
    if os.path.isdir(internal) and internal not in sys.path:
        sys.path.insert(0, internal)  # 保险：纯Python包也能被找到
    nl = os.path.join(internal, "numpy.libs")
    if os.path.isdir(nl):
        os.environ["PATH"] = nl + os.pathsep + os.environ.get("PATH", "")

# 让 PyInstaller 负责收集依赖，不在运行期改 sys.path
import numpy as np
import hnswlib
from sentence_transformers import SentenceTransformer

def _base_dir():
    """返回资源根目录：开发态用源码目录；打包态用 _MEIPASS（onefile）或 EXE 目录（onedir）"""
    if getattr(sys, "frozen", False):
        # onefile: 临时解压到 _MEIPASS；onedir: 可执行文件所在目录
        return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
    # 开发态
    return os.path.dirname(os.path.abspath(__file__))

def get_resource_path(relative_path: str) -> str:
    """兼容开发/打包的资源定位"""
    base = _base_dir()
    # 优先 base/relative_path；也兼容你原来放在同级的结构
    candidates = [
        os.path.join(base, relative_path),                 # _MEIPASS 或 EXE 目录下
        os.path.join(os.path.dirname(base), relative_path) # 有时资源会在上一层
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    # 找不到就返回第一个候选，方便暴露错误
    return candidates[0]

class LocalRetriever:
    def __init__(self, model_dir: str, index_dir: str, dim: int = 768):
        self.model_dir = model_dir
        self.index_dir = index_dir
        os.makedirs(get_resource_path(index_dir), exist_ok=True)
        self.dim = dim
        self.model = None
        self.index = None
        self.id2text = {}
        self._load_all()

    def _load_model(self):
        # 离线加载（避免在线下载）
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
        embs = self.model.encode(texts, batch_size=32, normalize_embeddings=True)
        embs = np.array(embs, dtype=np.float32)
        p = hnswlib.Index(space="cosine", dim=embs.shape[1])
        p.init_index(max_elements=len(texts), ef_construction=ef_construction, M=M)
        p.add_items(embs, ids=np.arange(len(texts)))
        p.set_ef(64)
        self.index = p
        self.id2text = {str(i): texts[i] for i in range(len(texts))}
        out_dir = get_resource_path(self.index_dir)
        os.makedirs(out_dir, exist_ok=True)
        p.save_index(os.path.join(out_dir, "kb.index"))
        with open(os.path.join(out_dir, "id2text.json"), "w", encoding="utf-8") as f:
            json.dump(self.id2text, f, ensure_ascii=False)

    def search(self, query: str, top_k=3):
        if not self.index:
            return []
        q = self.model.encode([query], normalize_embeddings=True)
        labels, dists = self.index.knn_query(q, k=min(top_k, len(self.id2text)))
        return [(self.id2text.get(str(i), ""), float(score)) for i, score in zip(labels[0], dists[0])]
