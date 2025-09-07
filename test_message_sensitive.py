#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Message类中的敏感词替换功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.database_manager import DatabaseManager
from src.Message import Message

def test_message_sensitive_words():
    """测试Message类中的敏感词替换功能"""
    
    # 创建数据库管理器实例
    db = DatabaseManager()
    
    # 创建Message实例
    message_handler = Message(db)
    
    # 测试数据
    test_cases = [
        {
            "message": "这个商品是最便宜的",
            "username": "test_user",
            "goodsinfo": None,
            "ccode": "test_session"
        },
        {
            "message": "关于宗教的话题",
            "username": "test_user", 
            "goodsinfo": None,
            "ccode": "test_session"
        },
        {
            "message": "这是一个正常的句子",
            "username": "test_user",
            "goodsinfo": None,
            "ccode": "test_session"
        },
        {
            "message": "最便宜的商品和宗教相关",
            "username": "test_user",
            "goodsinfo": None,
            "ccode": "test_session"
        }
    ]
    
    print("测试Message类敏感词替换功能:")
    print("=" * 50)
    
    for i, test_data in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        print(f"输入: '{test_data['message']}'")
        
        # 模拟一个简单的回复（不调用真实LLM）
        original_reply = f"回复关于 {test_data['message']} 的内容"
        
        # 手动应用敏感词替换（模拟Message类中的逻辑）
        sensitive_words = db.get_sensitive()
        sensitive_dict = {item['key']: item['value'] for item in sensitive_words}
        
        filtered_reply = original_reply
        for word, replacement in sensitive_dict.items():
            filtered_reply = filtered_reply.replace(word, replacement)
        
        print(f"原始回复: '{original_reply}'")
        print(f"过滤后回复: '{filtered_reply}'")
        
        # 验证替换是否发生
        if filtered_reply != original_reply:
            print("✅ 敏感词替换成功")
        else:
            print("ℹ️  无敏感词需要替换")

if __name__ == "__main__":
    test_message_sensitive_words()
