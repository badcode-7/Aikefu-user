import grpc
from concurrent import futures
import os
import sys
from . import api_pb2, api_pb2_grpc
from ..knowledge_base.core.retriever import LocalRetriever

class KnowledgeServicer(api_pb2_grpc.KnowledgeServiceServicer):
    def __init__(self):
        self.retriever = None
        
    def BuildIndex(self, request, context):
        try:
            self.retriever = LocalRetriever(
                model_dir=request.model_dir,
                index_dir=request.index_dir,
                dim=768
            )
            
            # 从build_index_once.py迁移的索引构建逻辑
            import glob
            def load_kb(kb_dir):
                texts = []
                for p in glob.glob(os.path.join(kb_dir, "*.*")):
                    if p.endswith((".txt",".md")):
                        with open(p, "r", encoding="utf-8") as f:
                            content = f.read()
                            texts += [line.strip() for line in content.splitlines() if line.strip()]
                return texts
                
            texts = load_kb(request.kb_dir)
            self.retriever.build_from_texts(texts)
            
            return api_pb2.BuildIndexResponse(
                success=True,
                message=f"Index built with {len(texts)} documents",
                document_count=len(texts)
            )
        except Exception as e:
            return api_pb2.BuildIndexResponse(
                success=False,
                message=str(e),
                document_count=0
            )
    
    def Search(self, request, context):
        if not self.retriever:
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details('Index not built')
            return api_pb2.SearchResponse()
            
        results = self.retriever.search(request.query, request.top_k)
        return api_pb2.SearchResponse(
            results=[api_pb2.SearchResponse.Result(text=r[0], score=r[1]) 
                   for r in results]
        )
    
    def GetStatus(self, request, context):
        return api_pb2.StatusResponse(
            ready=self.retriever is not None,
            version="1.0"
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    api_pb2_grpc.add_KnowledgeServiceServicer_to_server(
        KnowledgeServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
