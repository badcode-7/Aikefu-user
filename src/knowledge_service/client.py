import grpc
from . import api_pb2, api_pb2_grpc

class KnowledgeClient:
    def __init__(self, address='localhost:50051'):
        self.channel = grpc.insecure_channel(address)
        self.stub = api_pb2_grpc.KnowledgeServiceStub(self.channel)
        
    def build_index(self, kb_dir, model_dir, index_dir):
        request = api_pb2.BuildIndexRequest(
            kb_dir=kb_dir,
            model_dir=model_dir,
            index_dir=index_dir
        )
        return self.stub.BuildIndex(request)
        
    def search(self, query, top_k=3):
        request = api_pb2.SearchRequest(
            query=query,
            top_k=top_k
        )
        response = self.stub.Search(request)
        return [(r.text, r.score) for r in response.results]
        
    def get_status(self):
        return self.stub.GetStatus(api_pb2.StatusRequest())

    def close(self):
        self.channel.close()

# 兼容旧接口的包装器
class LocalRetrieverProxy:
    def __init__(self, model_dir, index_dir, dim=768):
        self.client = KnowledgeClient()
        self.model_dir = model_dir
        self.index_dir = index_dir
        self.dim = dim
        
    def search(self, query, top_k=3):
        return self.client.search(query, top_k)
        
    def build_from_texts(self, texts, ef_construction=200, M=16):
        """Send texts to service for indexing"""
        request = api_pb2.BuildFromTextsRequest(
            texts=texts,
            model_dir=self.model_dir,
            index_dir=self.index_dir,
            ef_construction=ef_construction,
            M=M
        )
        return self.client.stub.BuildFromTexts(request)

    def _load_model(self):
        """No-op in proxy - handled by service"""
        pass

    def _load_index(self):
        """No-op in proxy - handled by service"""
        pass

    def _load_all(self):
        """No-op in proxy - handled by service"""
        pass
