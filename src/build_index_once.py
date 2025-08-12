# build_index_once.py
import glob, os
from retriever import LocalRetriever

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
    texts = load_kb("./knowledge_data")
    r = LocalRetriever(model_dir="./models/bge-small-zh-v1.5",
                       index_dir="./rag_index",
                       dim=768)  # bge-small-zh 是 768 维
    r.build_from_texts(texts)
    print("索引构建完成，段落数：", len(texts))
