import sqlite3
import json
import os
from contextlib import closing
from PySide6.QtWidgets import QMessageBox,QWidget
import requests
from constants import AUTH_BASE  # 新

SERVER_URL = AUTH_BASE  # 改成你自己的服务（当前只有 /register /login /users/me /health）

class Database:
    def __init__(self, db_name):
        self.db_name = db_name

    def _connect(self):
        return sqlite3.connect(self.db_name)

    def execute(self, query, params=()):
        with closing(self._connect()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(query, params)
                connection.commit()
                return cursor

    def fetchall(self, query, params=()):
        with closing(self._connect()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()

    def fetchone(self, query, params=()):
        with closing(self._connect()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(query, params)
                return cursor.fetchone()

    def insert(self, query, params):
        cursor = self.execute(query, params)
        return cursor.lastrowid

    def update(self, query, params):
        self.execute(query, params)

    def delete(self, query, params):
        self.execute(query, params)



class SystemInfo:
    def __init__(self, db):
        self.db = db

    def get_system_info(self):
        query = 'SELECT * FROM system_info'
        return self.db.fetchone(query)

    def update_system_info(self, **kwargs):
        # 构建更新字段和参数
        fields = ", ".join(f"{key} = ?" for key in kwargs)
        query = f"UPDATE system_info SET {fields} WHERE id = 1"  # 只有一条记录，假设 id = 1
        self.db.update(query, tuple(kwargs.values()))



class DatabaseManager:
    def __init__(self, db_name='app_data.db'):
        self.db_name = db_name
        self.db = Database(self.db_name)

    def show_login_expired_error(self):
        temp_widget = QWidget()
        QMessageBox.critical(temp_widget, "错误", "当前登录已过期，请重新登录")

    def Ajax(self, url, headers=None, params=None, data=None, method='GET', json=None):
        """
        通用请求适配器
        - 你的认证服务只用到了 Bearer 头，目前其余业务都未实现，先不调用外部 API。
        """
        token = (self.get_system_info() or [""]*12)[11]  # 兼容空表
        headers = headers or {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

        url = f'{SERVER_URL}{url}'
        try:
            resp = requests.request(method, url, headers=headers, params=params, data=data, json=json, timeout=8)
            # FastAPI 未登录通常返回 401
            if resp.status_code == 401:
                self.show_login_expired_error()
                self.update_system_info(auto_login=0)
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as err:
            raise Exception(f'请求失败: {err}')

    # ===== 已实现的鉴权相关（可选封装） =====
    def auth_me(self):
        r = self.Ajax('/users/me')
        return r.json()

    # ======= 以下为【临时占位/本地假数据】========
    # 关键词相关（先返回空数据以保证 UI 不报错）
    def get_keywords(self):
        return []  # TODO: 等后端实现 /chatkeywords/list 后替换

    def getkeyword(self, id):
        return None

    def get_stoetkeywords(self, stortid):
        return []

    def _load_sensitive_words(self):
        """加载敏感词JSON文件"""
        sensitive_file = 'data/sensitive_words.json'
        if os.path.exists(sensitive_file):
            try:
                with open(sensitive_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}

    def _save_sensitive_words(self, sensitive_words):
        """保存敏感词到JSON文件"""
        sensitive_file = 'data/sensitive_words.json'
        os.makedirs(os.path.dirname(sensitive_file), exist_ok=True)
        with open(sensitive_file, 'w', encoding='utf-8') as f:
            json.dump(sensitive_words, f, ensure_ascii=False, indent=2)

    def get_sensitive(self):
        """获取所有敏感词"""
        sensitive_words = self._load_sensitive_words()
        return [{"id": i, "key": word, "value": replacement} 
                for i, (word, replacement) in enumerate(sensitive_words.items())]

    def add_keyword(self, keyword, content, store_id=0, type=1):
        # 敏感词添加逻辑
        if type == 2:  # 敏感词类型
            sensitive_words = self._load_sensitive_words()
            sensitive_words[keyword] = content
            self._save_sensitive_words(sensitive_words)
            return {'id': len(sensitive_words) - 1, 'key': keyword, 'value': content, 'type': type}
        # 先本地假返回
        return {'id': -1, 'key': keyword, 'value': content, 'type': type}

    def update_keyword(self, keyword_id, keyword, content):
        # 敏感词更新逻辑
        sensitive_words = self._load_sensitive_words()
        # 找到对应的敏感词并更新
        for i, (word, replacement) in enumerate(sensitive_words.items()):
            if i == keyword_id:
                # 删除旧的，添加新的
                del sensitive_words[word]
                sensitive_words[keyword] = content
                self._save_sensitive_words(sensitive_words)
                return {'id': keyword_id, 'key': keyword, 'value': content}
        return {'id': keyword_id, 'key': keyword, 'value': content}

    def delete_keyword(self, keyword_id):
        # 敏感词删除逻辑
        sensitive_words = self._load_sensitive_words()
        # 找到对应的敏感词并删除
        for i, (word, replacement) in enumerate(list(sensitive_words.items())):
            if i == keyword_id:
                del sensitive_words[word]
                self._save_sensitive_words(sensitive_words)
                return True
        return True

    def get_userinfo(self, token):
        # 现在直接走 /users/me
        try:
            return self.auth_me()
        except Exception:
            return {"username": "", "email": "", "mobile": "", "birthday": ""}

    # 其余商品、聊天等功能全部先返回空
    def get_association(self, data): return None
    def add_association(self, data): return None
    def get_goods(self, name): return None
    def save_chatlog(self, data): return None
    def get_goodsByProductId(self, product_id): return None
    def get_goodsByid(self, id, type=1): return None
    def add_goods(self, *args, **kwargs): return {"ok": False, "msg": "未实现"}
    def update_goods(self, *args, **kwargs): return {"ok": False, "msg": "未实现"}
    def get_goodslist(self, type=1): return []
    def delete_goods(self, id): return True
    
    # 新增：商品链接知识库关联功能（直接保存到文件，不使用数据库）
    def add_product_knowledge(self, product_url, product_name, shop_name, welcome_word, instructions, knowledge_content, product_id=None):
        """添加商品链接和知识库内容的关联（包含所有UI信息）- 直接保存到文件"""
        try:
            # 直接保存到知识库文件（包含所有信息）
            self._save_knowledge_to_file(
                product_url=product_url,
                product_name=product_name,
                shop_name=shop_name,
                welcome_word=welcome_word,
                instructions=instructions,
                knowledge_content=knowledge_content,
                product_id=product_id
            )
            
            return {"ok": True, "msg": "保存成功"}
        except Exception as e:
            return {"ok": False, "msg": f"保存失败: {str(e)}"}
    
    def _save_knowledge_to_file(self, product_url, product_name, shop_name, welcome_word, instructions, knowledge_content, product_id=None):
        """将知识库内容保存到文件，并发送到知识库服务（包含所有UI信息）"""
        try:
            # 创建商品说明书目录
            product_manual_dir = os.path.join("kb_engine", "resources", "knowledge_data", "product_manuals")
            os.makedirs(product_manual_dir, exist_ok=True)
            
            # 生成文件名（使用商品名称和URL的哈希值）
            import hashlib
            filename_hash = hashlib.md5(f"{product_name}_{product_url}".encode()).hexdigest()[:8]
            safe_product_name = "".join(c for c in product_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_product_name}_{filename_hash}.md"
            filepath = os.path.join(product_manual_dir, filename)
            
            # 获取当前时间
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 写入规范的文件内容（包含所有UI信息）
            file_content = f"""# {product_name}

## 基本信息
- **商品链接**: {product_url}
- **店铺名称**: {shop_name}
- **商品ID**: {product_id or '未提取'}
- **创建时间**: {current_time}

## 欢迎语
{welcome_word}

## 商品说明书
{instructions}

## 知识库内容
{knowledge_content}

---
*本文件由AI客服系统自动生成，包含商品的完整信息用于知识库检索。*
"""
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            # 发送到知识库服务
            self._send_to_kb_service(filepath, filename, file_content)
            
        except Exception as e:
            print(f"保存知识库文件失败: {e}")
    
    def _send_to_kb_service(self, filepath, filename, content):
        """发送知识库内容到知识库服务"""
        try:
            from kb_client import KBClient
            kb_client = KBClient(base_url="http://127.0.0.1:38999")
            
            # 尝试发送到知识库服务
            response = kb_client.add_file(filename=filename, content=content, rebuild=False)
            print(f"知识库服务响应: {response}")
            
        except Exception as e:
            print(f"发送到知识库服务失败: {e}")
            # 如果服务不可用，只保存文件，下次启动时会自动重建索引
    
    def get_knowledge_by_url(self, product_url):
        """根据商品链接获取知识库内容（从文件系统读取）"""
        try:
            # 从文件系统查找对应的知识库文件
            product_manual_dir = os.path.join("kb_engine", "resources", "knowledge_data", "product_manuals")
            if not os.path.exists(product_manual_dir):
                return None
                
            # 遍历所有文件，查找包含该URL的文件
            for filename in os.listdir(product_manual_dir):
                if filename.endswith('.md'):
                    filepath = os.path.join(product_manual_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # 检查文件内容是否包含该商品链接
                            if product_url in content:
                                # 提取知识库内容部分
                                lines = content.split('\n')
                                knowledge_start = False
                                knowledge_content = []
                                
                                for line in lines:
                                    if line.strip() == '## 知识库内容':
                                        knowledge_start = True
                                        continue
                                    elif knowledge_start and line.strip().startswith('##'):
                                        break
                                    elif knowledge_start and line.strip():
                                        knowledge_content.append(line.strip())
                                
                                if knowledge_content:
                                    return '\n'.join(knowledge_content)
                    except Exception:
                        continue
            return None
        except Exception:
            return None
    
    def get_all_product_knowledge(self):
        """获取所有商品知识库记录（从文件系统读取）"""
        try:
            product_manual_dir = os.path.join("kb_engine", "resources", "knowledge_data", "product_manuals")
            if not os.path.exists(product_manual_dir):
                return []
                
            knowledge_list = []
            # 遍历所有知识库文件
            for filename in os.listdir(product_manual_dir):
                if filename.endswith('.md'):
                    filepath = os.path.join(product_manual_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            # 从文件名提取信息
                            product_name = filename.replace('.md', '').split('_')[0]
                            
                            # 从文件内容提取信息
                            lines = content.split('\n')
                            product_url = ""
                            shop_name = ""
                            knowledge_content = []
                            knowledge_start = False
                            
                            for line in lines:
                                if line.startswith('- **商品链接**:'):
                                    product_url = line.replace('- **商品链接**:', '').strip()
                                elif line.startswith('- **店铺名称**:'):
                                    shop_name = line.replace('- **店铺名称**:', '').strip()
                                elif line.strip() == '## 知识库内容':
                                    knowledge_start = True
                                    continue
                                elif knowledge_start and line.strip().startswith('##'):
                                    break
                                elif knowledge_start and line.strip():
                                    knowledge_content.append(line.strip())
                            
                            if product_url and product_name:
                                knowledge_list.append({
                                    "id": len(knowledge_list) + 1,  # 生成虚拟ID
                                    "product_url": product_url,
                                    "product_name": product_name,
                                    "shop_name": shop_name,
                                    "knowledge_content": '\n'.join(knowledge_content) if knowledge_content else ""
                                })
                    except Exception:
                        continue
            
            return knowledge_list
        except Exception:
            return []
    
    def update_product_knowledge(self, id, knowledge_content):
        """更新商品知识库内容（通过文件系统）"""
        try:
            # 从文件系统获取所有知识库记录
            knowledge_list = self.get_all_product_knowledge()
            if id <= 0 or id > len(knowledge_list):
                return False
                
            # 获取要更新的记录
            target_record = knowledge_list[id - 1]
            product_url = target_record["product_url"]
            product_name = target_record["product_name"]
            shop_name = target_record["shop_name"]
            
            # 重新保存文件（包含新的知识库内容）
            self._save_knowledge_to_file(
                product_url=product_url,
                product_name=product_name,
                shop_name=shop_name,
                welcome_word="",  # 这些信息需要从原文件中提取，暂时留空
                instructions="",  # 这些信息需要从原文件中提取，暂时留空
                knowledge_content=knowledge_content,
                product_id=None
            )
            
            return True
        except Exception as e:
            print(f"更新知识库失败: {e}")
            return False
    
    def delete_product_knowledge(self, id):
        """删除商品知识库记录（通过文件系统）"""
        try:
            # 从文件系统获取所有知识库记录
            knowledge_list = self.get_all_product_knowledge()
            if id <= 0 or id > len(knowledge_list):
                return False
                
            # 获取要删除的记录
            target_record = knowledge_list[id - 1]
            product_url = target_record["product_url"]
            product_name = target_record["product_name"]
            
            # 删除对应的知识库文件
            self._delete_knowledge_file(product_url, product_name)
            
            return True
        except Exception:
            return False
    
    def _delete_knowledge_file(self, product_url, product_name):
        """删除对应的知识库文件"""
        try:
            import hashlib
            filename_hash = hashlib.md5(f"{product_name}_{product_url}".encode()).hexdigest()[:8]
            safe_product_name = "".join(c for c in product_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_product_name}_{filename_hash}.md"
            
            product_manual_dir = os.path.join("kb_engine", "resources", "knowledge_data", "product_manuals")
            filepath = os.path.join(product_manual_dir, filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"已删除知识库文件: {filepath}")
                
        except Exception as e:
            print(f"删除知识库文件失败: {e}")
