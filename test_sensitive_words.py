#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.database_manager import DatabaseManager

def test_sensitive_words():
    """测试敏感词功能"""
    print("=== 测试敏感词功能 ===")
    
    # 创建数据库管理器实例
    db_manager = DatabaseManager()
    
    # 测试1: 获取当前敏感词
    print("\n1. 获取当前敏感词列表:")
    sensitive_words = db_manager.get_sensitive()
    print(f"当前敏感词: {sensitive_words}")
    
    # 测试2: 添加新的敏感词
    print("\n2. 添加新的敏感词:")
    new_word = db_manager.add_keyword("测试敏感词", "替换内容", type=2)
    print(f"添加成功: {new_word}")
    
    # 测试3: 再次获取敏感词列表
    print("\n3. 再次获取敏感词列表:")
    sensitive_words = db_manager.get_sensitive()
    print(f"更新后的敏感词: {sensitive_words}")
    
    # 测试4: 测试敏感词替换功能
    print("\n4. 测试敏感词替换功能:")
    test_text = "这是一个测试敏感词的文本，包含最便宜和宗教内容"
    print(f"原始文本: {test_text}")
    
    # 模拟敏感词替换逻辑
    sensitive_data = db_manager._load_sensitive_words()
    for word, replacement in sensitive_data.items():
        test_text = test_text.replace(word, replacement)
    
    print(f"替换后文本: {test_text}")
    
    # 测试5: 删除敏感词
    print("\n5. 删除刚才添加的敏感词:")
    if sensitive_words:
        # 找到刚才添加的测试敏感词
        test_word_id = None
        for word in sensitive_words:
            if word['key'] == "测试敏感词":
                test_word_id = word['id']
                break
        
        if test_word_id is not None:
            result = db_manager.delete_keyword(test_word_id)
            print(f"删除结果: {result}")
            
            # 验证删除
            sensitive_words = db_manager.get_sensitive()
            print(f"删除后的敏感词列表: {sensitive_words}")
        else:
            print("未找到测试敏感词")
    else:
        print("没有敏感词可删除")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_sensitive_words()
