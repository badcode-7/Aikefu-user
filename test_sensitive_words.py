#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试敏感词替换功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.database_manager import DatabaseManager

def test_sensitive_words():
    """测试敏感词替换功能"""
    
    # 创建数据库管理器实例
    db = DatabaseManager()
    
    # 测试获取敏感词
    sensitive_words = db.get_sensitive()
    print("当前敏感词列表:")
    for word in sensitive_words:
        print(f"  {word['key']} -> {word['value']}")
    
    # 测试敏感词替换
    test_texts = [
        "这个商品是最便宜的",
        "关于宗教的话题",
        "这是一个正常的句子",
        "最便宜的商品和宗教相关"
    ]
    
    print("\n测试敏感词替换:")
    for text in test_texts:
        original = text
        for word in sensitive_words:
            text = text.replace(word['key'], word['value'])
        print(f"  '{original}' -> '{text}'")

if __name__ == "__main__":
    test_sensitive_words()
