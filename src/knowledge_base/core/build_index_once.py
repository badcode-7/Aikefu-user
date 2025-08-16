# build_index_once.py
import glob
import os
import sys
from .retriever import LocalRetriever

def get_resource_path(relative_path):
    """获取打包后资源的绝对路径"""
    try:
        base_path = sys._MEIPASS  # PyInstaller创建的临时文件夹
    except AttributeError:
        base_path = os.path.abspath(".")  # 开发环境
    
    return os.path.join(base_path, relative_path)

def split_text(s: str, max_len=300):
    buf, out = "", []
    for line in s.splitlines():
        line = line.strip()
        if not line: continue
        if len(buf) + len(line) + 1 > max_len:
            out.append(buf); buf = line
        else:
            buf = (buf + "\n" + line) if buf else line
    if buf: out.append(buf)
    return out

def load_kb(kb_dir: str):
    texts = []
    for p in glob.glob(os.path.join(kb_dir, "*.*")):
        if p.endswith((".txt",".md")):
            with open(p, "r", encoding="utf-8") as f:
                texts += split_text(f.read())
    return texts

if __name__ == "__main__":
    kb_dir = get_resource_path("src/knowledge_base/knowledge_data")
    model_dir = get_resource_path("src/models/bge-small-zh-v1.5")
    index_dir = get_resource_path("src/knowledge_base/rag_index")
    
    texts = load_kb(kb_dir)
    r = LocalRetriever(model_dir=model_dir,
                       index_dir=index_dir,
                       dim=768)  # bge-small-zh 是 768 维
    r.build_from_texts(texts)
    print("索引构建完成，段落数：", len(texts))
