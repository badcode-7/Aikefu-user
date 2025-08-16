from typing import List, Tuple

class KnowledgeBase:
    """知识库核心接口"""
    
    def __init__(self, model_dir: str, index_dir: str):
        """
        初始化知识库
        :param model_dir: 模型目录路径
        :param index_dir: 索引目录路径
        """
        self.model_dir = model_dir
        self.index_dir = index_dir

    def add_document(self, file_path: str) -> bool:
        """添加单个知识文档"""
        raise NotImplementedError

    def rebuild_index(self) -> bool:
        """重建整个知识库索引"""
        raise NotImplementedError
        
    def query(self, question: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """查询知识库"""
        raise NotImplementedError


class KnowledgeBaseFactory:
    """知识库工厂类"""
    
    @staticmethod
    def create_knowledge_base(model_dir: str, index_dir: str) -> KnowledgeBase:
        """
        创建知识库实例
        :param model_dir: 模型目录路径
        :param index_dir: 索引目录路径
        :return: KnowledgeBase实例
        """
        from .core.retriever import LocalRetriever
        return LocalRetriever(model_dir, index_dir)
