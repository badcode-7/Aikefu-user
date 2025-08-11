import sqlite3
from contextlib import closing
from PySide6.QtWidgets import QMessageBox,QWidget
import requests
from app.constants import AUTH_BASE  # 新

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

    def get_sensitive(self):
        return []

    def add_keyword(self, keyword, content, store_id=0, type=1):
        # 先本地假返回
        return {'id': -1, 'key': keyword, 'value': content, 'type': type}

    def update_keyword(self, keyword_id, keyword, content):
        return {'id': keyword_id, 'key': keyword, 'value': content}

    def delete_keyword(self, keyword_id):
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

