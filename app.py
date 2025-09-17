from data.database_manager import DatabaseManager
from kb_client import KBClient, KBServiceManager

from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt, QModelIndex, Slot, QCoreApplication, QTimer
from PySide6.QtWidgets import QMessageBox, QMainWindow, QGraphicsDropShadowEffect, QTableWidgetItem, QMenu, QTableWidgetItem, QListWidget, QVBoxLayout, QApplication, QPushButton
from PySide6.QtGui import QAction, QColor

from src.WebSocketServer import WebSocketServer
from src.MessageDispatcher import MessageDispatcher
from src.Message import Message
from flask import Flask, send_file, request, jsonify
from flask_sslify import SSLify
from threading import Lock, Thread
from pathlib import Path
import sys
import os

def get_resource_path(relative_path):
    """获取打包后资源的绝对路径"""
    try:
        base_path = sys._MEIPASS  # PyInstaller创建的临时文件夹
    except AttributeError:
        base_path = os.path.abspath(".")  # 开发环境
    
    return os.path.join(base_path, relative_path)

from src.ui.home import Ui_MainWindow
from src.ui.login import Ui_LoginPage
from src.Updata import Updata
from constants import AUTH_BASE

import webbrowser
import requests
import threading
import faulthandler
import atexit
import pyautogui
import json
import threading
import queue
import requests
import os
import ssl
import time
import signal
import requests
import webbrowser
import sys
import traceback
import win32gui
import win32con
import win32api
import win32process
import shutil
import subprocess

task_queue = queue.Queue()
flask_app = None
ws_server = None
current_version = "1.0.0.13"

# 全局异常与 Qt 消息钩子，避免异常直接导致程序退出
def _write_crash_log(prefix: str, content: str):
    try:
        with open('crash.log', 'a', encoding='utf-8') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {prefix}: {content}\n\n")
    except Exception:
        pass

def _excepthook(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        return
    tb = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print("未捕获异常：", tb)
    _write_crash_log('PY', tb)

def _qt_message_handler(mode, context, message):
    try:
        _write_crash_log('QT', f"{message}")
    except Exception:
        pass

# 捕获线程中的未处理异常（Python 3.8+）
def _thread_excepthook(args):
    try:
        tb = ''.join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
        print("线程异常：", tb)
        _write_crash_log('TH', tb)
    except Exception:
        pass

# 启用 faulthandler，捕获崩溃信号和死锁堆栈
_faulthandler_file = None
def _enable_faulthandler():
    global _faulthandler_file
    try:
        _faulthandler_file = open('faulthandler.log', 'a', encoding='utf-8')
        faulthandler.enable(_faulthandler_file)
    except Exception:
        pass

def _disable_faulthandler():
    global _faulthandler_file
    try:
        if _faulthandler_file:
            _faulthandler_file.flush()
            _faulthandler_file.close()
    except Exception:
        pass

# 登录
class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 实例化 Ui_MainWindow 并设置 UI
        db_manager = DatabaseManager()
        self.db = db_manager
        # system_info = db_manager.get_system_info()
        self.sinfo = True

        self.ui = Ui_LoginPage()
        self.ui.setupUi(self)
        # if self.sinfo[7]:
        #     self.ui.username.setText(self.sinfo[7])
        # if self.sinfo[5] and self.sinfo[8]:
        #     self.ui.checkBox.setChecked(True)
        #     self.ui.password.setText(self.sinfo[8])
        # if self.sinfo[6]:
        #     self.ui.checkBox_2.setChecked(True)

        # self.ui.checkBox_2.clicked.connect(self.change_checkBox)
        # self.ui.checkBox.clicked.connect(self.change_checkBox)
        # self.ui.pushButton_3.clicked.connect(self.gotoregister)
        # self.ui.pushButton_4.clicked.connect(self.gotoresetpwd)
        # 绑定登录事件
        self.ui.loginBut.clicked.connect(self.login)
        # 设置无标题窗口
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        # 设置背景透明
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)  # 阴影的模糊半径
        shadow.setColor(QColor(0, 0, 0, 255))  # 阴影的颜色和透明度
        shadow.setOffset(0, 0)  # 阴影的偏移量
        # 将阴影效果添加到按钮上
        self.ui.mainBox.setGraphicsEffect(shadow)
        self.ui.label_4.setText("版本号：" + current_version)
        self.delayed_login_timer = QTimer(self)
        self.delayed_login_timer.setSingleShot(True)  # 设置为单次触发
        self.delayed_login_timer.timeout.connect(
            self.check_and_login_if_needed)
        # 设置一个短暂的延迟，比如500毫秒
        self.delayed_login_timer.start(500)
        self.show()

    def check_and_login_if_needed(self):
        try:
            if isinstance(self.sinfo, (list, tuple)) and len(self.sinfo) > 6 and self.sinfo[6]:
                self.login()
        except Exception:
            pass


    def change_checkBox(self):
        if self.ui.checkBox.isChecked():
            self.db.update_system_info(save_password=1)
        else:
            self.db.update_system_info(save_password=0)
        if self.ui.checkBox_2.isChecked():
            self.ui.checkBox.setChecked(True)
            self.db.update_system_info(auto_login=1)
            self.db.update_system_info(save_password=1)
        else:
            self.db.update_system_info(auto_login=0)

    def login(self):
        username = self.ui.username.text()
        password = self.ui.password.text()
        if not username or not password:
            self.show_error_message("用户名和密码不能为空！")
            return

        # 修改为调用/aikefu/login端点
        try:
            r = requests.post(
                f"{AUTH_BASE}/aikefu/login",  # 修改这里
                json={"username": username, "password": password},
                timeout=8,
            )
        except Exception as e:
            self.show_error_message(f"登录请求失败：{e}")
            return

        # 以下保持原样（已处理VIP错误）
        if r.status_code == 401:
            try:
                error_detail = r.json().get("detail", "")
                if "非VIP用户" in error_detail:
                    self.show_error_message("非VIP用户无法登录，请升级VIP会员")
                else:
                    self.show_error_message("登录失败，请检查用户名或密码")
            except:
                self.show_error_message("登录失败，请检查用户名或密码")
            return
        elif r.status_code != 200:
            self.show_error_message("登录失败，请检查用户名或密码")
            return

        data = r.json()
        access_token = data.get("access_token")
        if not access_token:
            self.show_error_message("登录失败：未返回 access_token")
            return

        # 获取用户信息
        try:
            me = requests.get(
                f"{AUTH_BASE}/users/me",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=8,
            ).json()
        except Exception:
            me = {"username": username, "email": ""}

        self.homewin = HomeWindow()
        self.homewin.show()
        self.close()


    def show_error_message(self, message):
        # 显示错误消息
        msgbox = QMessageBox()
        msgbox.setIcon(QMessageBox.Information)
        msgbox.setText(message)
        msgbox.setStandardButtons(QMessageBox.Ok)
        msgbox.exec()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.isMaximized() == False:
            self.m_flag = True
            self.m_Position = event.globalPos() - self.pos()  # 获取鼠标相对窗口的位置
            event.accept()
            self.setCursor(QtGui.QCursor(QtCore.Qt.OpenHandCursor))  # 更改鼠标图标

    def mouseMoveEvent(self, mouse_event):
        if QtCore.Qt.LeftButton and self.m_flag:
            self.move(mouse_event.globalPos() - self.m_Position)  # 更改窗口位置
            mouse_event.accept()

    def mouseReleaseEvent(self, mouse_event):
        self.m_flag = False
        self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

    def gotoregister(self):
        webbrowser.open(f"{AUTH_BASE}/docs#/default/register_user_register_post")
        # 或者改为弹框提示“请在本客户端注册页使用”，如果你准备做本地注册窗体

    def gotoresetpwd(self):
        # 你的后端还没重置密码接口的话先简单提示
        self.show_error_message("重置密码功能暂未开放，请联系管理员")



# 这里进行js注入工作，注入的js文件可以自行编写，也可以使用我们提供的kelin.js文件
# 监听服务
class FlaskApp:
    def __init__(self,userinfo):
        self.app = Flask(__name__)
        self.sslify = SSLify(self.app, permanent=True)
        self.userinfo = userinfo
        self.run_dir = os.path.dirname(os.path.abspath(__file__))
        self.lock = Lock()
        self.ui = Ui_MainWindow()
        @self.app.route("/imsupport")
        def inject_js():
            js_resource_path = get_resource_path("src/plugins/kelin.js")
            return send_file(js_resource_path, mimetype='application/javascript')

    def modify_hosts(self):
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        try:
            # 尝试以管理员权限打开文件
            with open(hosts_path, 'r+', encoding='utf-8') as file:
                hosts_content = file.read()
                new_entry = "\n127.0.0.1 iseiya.taobao.com\n"
                if new_entry not in hosts_content:
                    file.seek(0, 2)
                    file.write(new_entry)
        except PermissionError:
            # 如果没有权限，显示提示信息
            print("请使用管理员权限运行程序。")
            # QMessageBox.warning(None, "权限错误", "请使用管理员权限运行程序。")
            return False
        except Exception as e:
            print(f"修改hosts文件时发生错误: {e}")
            return False
        return True

    def start_https_server(self, cert_path, key_path):
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile=cert_path, keyfile=key_path)
        try:
            http_thread = Thread(target=lambda: self.app.run(
                port=443, ssl_context=context))
            http_thread.start()
            print("启动成功")
            return True
        except Exception as e:
            print(f"启动失败,请联系管理员{e}")
            return False

    def init_message_listener(self):
        with self.lock:
            self.modify_hosts()
            cert_file = get_resource_path("src/plugins/server.crt")
            key_file = get_resource_path("src/plugins/server.key")
            print(key_file, 61)
            if not os.path.exists(cert_file) or not os.path.exists(key_file):
                # 输出错误信息
                print(f"启动失败,请联系管理员")
                return False
            https_success = self.start_https_server(cert_file, key_file)
            return https_success

    def shutdown(self):
        os.kill(os.getpid(), signal.SIGINT)

    def run(self):
        if not self.init_message_listener():
            print("消息监听初始化失败")
        else:
            print("消息监听初始化c成功")
            while True:
                if self.userinfo['vip'] == 1:
                    time.sleep(1)

# 首页
class HomeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 实例化 Ui_MainWindow 并设置 UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        db_manager = DatabaseManager()
        self.db = db_manager
        # self.system_info = self.db.get_system_info()                    # 获取系统信息
        # self.userinfo = self.db.get_userinfo(self.system_info[11])      # 获取用户信息              线上了

        self.keywords = self.db.get_keywords()                          # 获取关键词列表
        self.keywordskv = self.extract_keys(self.keywords)              # 提取关键词列表

        self.minganciData = self.db.get_sensitive()                     # 获取敏感词列表
        self.minganciDatakv = self.extract_keys(self.minganciData)      # 提取敏感词列表

        self.goodsList = self.db.get_goodslist()                        # 获取商品列表
        # self.ui.username.setText(self.userinfo['nickname'])
        # self.ui.emall.setText(self.userinfo['email'])
        # self.ui.phone.setText(self.userinfo['mobile'])
        # self.ui.birthday.setText(self.userinfo['birthday'])
        # 设置无标题窗口
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        # 设置背景透明
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)  # 阴影的模糊半径
        shadow.setColor(QColor(0, 0, 0, 255))  # 阴影的颜色和透明度
        shadow.setOffset(0, 0)  # 阴影的偏移量
        # 将阴影效果添加到按钮上
        self.ui.home.setGraphicsEffect(shadow)
        # 绑定按钮的点击事件
        # lambda:self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.mgctianjia.clicked.connect(self.add_new_sensitive)
        self.ui.home_but.clicked.connect(lambda: self.munuBut(0))
        self.ui.massg_but.clicked.connect(lambda: self.munuBut(1))  # 敏感词管理
        self.ui.keyword_but.clicked.connect(lambda: self.munuBut(2))  # 商品说明书
        # 隐藏/禁用未实现功能按钮
        # self.ui.massg_but.setEnabled(False)      # 敏感词管理 - 已实现，启用
        # self.ui.keyword_but.setEnabled(False)    # 关键词管理 - 现在启用商品说明书功能
        self.ui.my_but.setEnabled(False)
        self.ui.refresh.setEnabled(False)
        # self.ui.newgoodsBut.setEnabled(False)  # 启用添加商品按钮
        self.ui.modify.setEnabled(False)
        self.ui.about.setEnabled(False)
        
        # 启用关键词管理按钮（商品说明书）
        self.ui.keyword_but.setEnabled(True)
        
        # 绑定添加商品按钮事件
        self.ui.newgoodsBut.clicked.connect(lambda: self.add_new_goods(None, 1))
        
        # 确保添加商品按钮是启用的
        self.ui.newgoodsBut.setEnabled(True)
        
        # 启用系统设置按钮并绑定知识库功能
        self.ui.setup_but.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(3))
        # 列表清空并给出占位提示
        self.ui.listView.setEnabled(False)
        self.ui.listView2.setEnabled(False)

        
        # 加载关键词
        self.keyword_table = self.ui.tableWidget
        self.keyword_table.setColumnWidth(0, 100)
        self.keyword_table.setColumnWidth(1, 288)
        self.populate_table(self.keyword_table)
        self.keyword_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.keyword_table.customContextMenuRequested.connect(lambda pos: self.showContextMenu(pos, self.keyword_table))
        self.keyword_table.itemChanged.connect(self.item_changed)
        self.minganciTable = self.ui.minganciTable
        self.minganciTable.setColumnWidth(0, 180)
        self.minganciTable.setColumnWidth(1, 200)
        self.populate_tablea()
        self.minganciTable.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.minganciTable.customContextMenuRequested.connect(self.showContextMenuM)
        self.minganciTable.itemChanged.connect(self.minganci_changed)

        # 初始化系统设置
        # self.ui.tishici.setText(self.system_info[9])
        # self.ui.tishici2.setText(self.system_info[10])
        self.show()
        self.append_log_message(f"登录成功")

        # 获取config.json文件中的配置信息
        self.load_config()
        # 设置匹配度
        self.ui.pipeidu.setValue(self.pipeidu)
        
        # 加载配置到UI
        self.ui.tishici.setText(self.config.get("role_description", ""))
        self.ui.tishici2.setText(self.config.get("general_role_description", ""))
        self.ui.shop_description.setText(self.config.get("shop_description", ""))
        self.ui.ai_reply_style.setText(self.config.get("ai_reply_style", ""))
        # 绑定滑动事件
        self.ui.pipeidu.sliderMoved.connect(self.on_slider_moved)

        self.flask_thread = None
        self.ws_thread = None
        self.dispatcher = MessageDispatcher()
        
        flask_thread = threading.Thread(target=self.run_flask)
        flask_thread.start()
        ws_thread = threading.Thread(target=self.run_websocket)
        ws_thread.start()
        # 增加线程循环任务
        loop_task  =threading.Thread(target=self.loop_task)
        loop_task.start()
        self.ui.btn_diagnose = QPushButton("运行诊断")
        self.ui.btn_diagnose.clicked.connect(self.run_diagnosis)
        
        # 添加知识库管理功能
        self.ui.add_kb_btn.clicked.connect(self.add_knowledge_file)
        self.ui.rebuild_index_btn.clicked.connect(self.rebuild_knowledge_index)
        self.ui.product_kb_btn.clicked.connect(self.open_product_knowledge_manager)
        
        # 绑定保存按钮
        self.ui.updataBut.clicked.connect(self.updata_hosts)
        
        # 注入结束
        # 监听websocket服务
        self.dispatcher.message_received.connect(self.on_message_received)
        self.connectqianniu()# 连接千牛
  # 在日志区域上方添加诊断按钮
        self.ui.btn_diagnose = QPushButton("运行诊断", self.ui.home)
        self.ui.btn_diagnose.setGeometry(QtCore.QRect(20, 180, 100, 30))  # 调整位置和大小
        self.ui.btn_diagnose.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.ui.btn_diagnose.clicked.connect(self.run_diagnosis)
        # 添加线程池和消息队列
        self.message_queue = queue.Queue()
        self.max_workers = 5  # 最大工作线程数
        self.worker_threads = []
        self.is_running = True
        
        # 启动工作线程
        for _ in range(self.max_workers):
            worker = threading.Thread(target=self.message_processor)
            worker.daemon = True
            worker.start()
            self.worker_threads.append(worker)

        # 添加拼多多客服按钮
        self.ui.pdd_button = QPushButton("拼", self)
        self.ui.pdd_button.setStyleSheet("""
            QPushButton {
                background-color: #E02020;
                color: white;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FF2020;
            }
        """)
        self.ui.pdd_button.clicked.connect(self.open_pdd_window)
        self.ui.horizontalLayout.addWidget(self.ui.pdd_button)
        
        # 初始化浏览器窗口和测试服务器
        self.browser_window = None
        self.test_server_thread = None
        # —— 知识库服务集成 START ——
        self.kb_client = KBClient(base_url="http://127.0.0.1:38999")
        self.kb = self.kb_client
        self.kb_mgr = KBServiceManager(self.kb_client, log_fn=self.append_log_message)

        # 异步启动，不阻塞 UI
        self.kb_mgr.start_async()

        # 可选：等就绪后提示（不阻塞）
        def _poll_kb_ready():
            try:
                if self.kb_client.health().get("status") == "ok":
                    self.append_log_message("知识库引擎已就绪")
                    return
            except Exception:
                pass
            QtCore.QTimer.singleShot(1000, _poll_kb_ready)
        QtCore.QTimer.singleShot(1000, _poll_kb_ready)
        # —— 知识库服务集成 END ——
        self._ensure_kb()

        # 已在 QApplication 创建前设置 DPI 策略
    # 顶部：确保已导入
    from kb_client import KBClient, KBServiceManager

    def _ensure_kb(self):
        """确保 kb_client / kb_mgr 已初始化，并启动本地引擎"""
        if not hasattr(self, "kb_client") or self.kb_client is None:
            # 按你的端口/地址改
            self.kb_client = KBClient(base_url="http://127.0.0.1:38999")
            self.kb_mgr = KBServiceManager(self.kb_client, log_fn=self.append_log_message)
            self.kb_mgr.start_async()  # 后台启动引擎，不阻塞 UI

            # 兼容老代码如果还有 self.kb.xxx 的调用：
            self.kb = self.kb_client

            # 非阻塞健康检查提示（可选）
            QtCore.QTimer.singleShot(1500, lambda: self.append_log_message(
                f"KB健康：{self.kb_client.health()}"
            ))

    def check_js_environment(self):
            """检查JS执行环境"""
            try:
                # 查找调试标记
                marker_hwnd = win32gui.FindWindowEx(0, 0, None, "Kelin Injected")
                if marker_hwnd:
                    print("JS调试标记存在，表明JS已执行")
                    return True
                
                # 查找控制台窗口
                console_hwnd = win32gui.FindWindow("DevTools_WidgetDockWindow", None)
                if console_hwnd:
                    print("开发者工具已打开，可查看控制台日志")
                    return True
                    
                print("未找到JS执行证据")
                return False
            except Exception as e:
                print(f"环境检查错误: {str(e)}")
                return False
    def run_diagnosis(self):
        """运行全面诊断"""
        self.append_log_message("开始系统诊断...")
        
        # 1. 检查窗口是否存在
        parent_hwnd = win32gui.FindWindow("Qt5152QWindowIcon", "千牛接待台")
        if parent_hwnd:
            self.append_log_message(f"找到接待台窗口: 0x{parent_hwnd:X}")
        else:
            self.append_log_message("未找到接待台窗口")
        
        # 2. 检查子窗口
        child_hwnd = self.find_child_window(parent_hwnd, "千牛工作台", 3)
        if child_hwnd:
            self.append_log_message(f"找到工作台子窗口: 0x{child_hwnd:X}")
        else:
            self.append_log_message("未找到工作台子窗口")
        
        # 3. 检查JS环境
        if self.check_js_environment():
            self.append_log_message("JS环境检查通过")
        else:
            self.append_log_message("JS环境检查失败")
        
        # 4. 检查WebSocket连接
        if hasattr(self, 'ws_server') and self.ws_server.clients:
            client_count = len(self.ws_server.clients)
            self.append_log_message(f"WebSocket连接数: {client_count}")
        else:
            self.append_log_message("无活跃WebSocket连接")
        
        # 5. 检查Flask服务
        try:
            response = requests.get('https://iseiya.taobao.com/imsupport', 
                                verify=False, timeout=2)
            if response.status_code == 200:
                self.append_log_message("JS文件可访问")
            else:
                self.append_log_message(f"JS文件访问失败: HTTP {response.status_code}")
        except Exception as e:
            self.append_log_message(f"JS文件访问错误: {str(e)}")
        
        self.append_log_message("诊断完成")
        
    def check_js_environment(self):
        """检查JS执行环境"""
        try:
            # 查找调试标记
            marker_hwnd = win32gui.FindWindowEx(0, 0, None, "Kelin Injected")
            if marker_hwnd:
                print("JS调试标记存在，表明JS已执行")
                return True
            
            # 查找控制台窗口
            console_hwnd = win32gui.FindWindow("DevTools_WidgetDockWindow", None)
            if console_hwnd:
                print("开发者工具已打开，可查看控制台日志")
                return True
                
            print("未找到JS执行证据")
            return False
        except Exception as e:
            print(f"环境检查错误: {str(e)}")
            return False
    def open_pdd_window(self):
        """打开拼多多客服窗口"""
        from src.ui.browser import BrowserWindow
        from src.test_server import run_test_server
        import threading
        
        # 启动测试服务器（如果还没启动）
        if not self.test_server_thread:
            self.test_server_thread = threading.Thread(target=run_test_server, daemon=True)
            self.test_server_thread.start()
        
        # 创建新的浏览器窗口（如果还没创建）
        if not self.browser_window:
            self.browser_window = BrowserWindow()
        
        # 显示窗口
        self.browser_window.show()
        self.browser_window.raise_()

    # 循环任务
    def loop_task(self):
        while True:
            try:
                self.avoid_send_failure()
                # self.update_goods_list()
            except Exception as e:
                print(e)
    # 滑动事件
    def load_config(self):
        """加载配置文件"""
        config_file = 'data/config.json'
        default_config = {
            "pipeidu": 57,
            "role_description": "",
            "general_role_description": "",
            "shop_description": "",
            "ai_reply_style": ""
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                    # 确保所有配置项都存在
                    for key, value in default_config.items():
                        if key not in self.config:
                            self.config[key] = value
            else:
                self.config = default_config
                self.save_config()
                
            # 设置匹配度
            self.pipeidu = self.config.get("pipeidu", 57)
            
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            self.config = default_config
            self.pipeidu = 57

    def save_config(self):
        """保存配置文件"""
        config_file = 'data/config.json'
        try:
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def on_slider_moved(self, event):
        value = self.ui.pipeidu.value()
        # 将值传递给config.json文件
        self.pipeidu = value
        self.config["pipeidu"] = value
        self.save_config()

    def extract_keys(self, keyword_list):
        if keyword_list is None:
            return {}
        else:
            return {keyword['key']: keyword['value'] for keyword in keyword_list}

    # 打开指定网页
    def openweb(self, url):
        webbrowser.open(url)

    # 菜单样式重置
    def reset_menu_style(self):
        self.ui.home_but.setStyleSheet("image: url(:/icon/icon/首页.png);background-image:none;")
        self.ui.massg_but.setStyleSheet("image: url(:/icon/icon/敏感词.png);background-image: none;")
        self.ui.keyword_but.setStyleSheet("image: url(:/icon/icon/minganci.png);background-image: none;")
        self.ui.setup_but.setStyleSheet("image: url(:/icon/icon/设置.png);background-image: none;")
        self.ui.my_but.setStyleSheet("image: url(:/icon/icon/我的.png);background-image: none;")

    # 左侧菜单点击事件
    def munuBut(self, index):
        self.ui.stackedWidget.setCurrentIndex(index)
        if index == 0:
            # self.ui.home_top_title.setText("科智智能客服")
            self.reset_menu_style()
            self.ui.home_but.setStyleSheet("background-image: url(:/icon/icon/选中圆.png);image: url(:/icon/icon/首页.png);")
        elif index == 1:
            # self.ui.home_top_title.setText("敏感词管理")
            self.reset_menu_style()
            self.ui.massg_but.setStyleSheet("background-image: url(:/icon/icon/选中圆.png);image: url(:/icon/icon/敏感词.png);")
        elif index == 2:
            # self.ui.home_top_title.setText("商品说明书")
            self.reset_menu_style()
            self.ui.keyword_but.setStyleSheet("background-image: url(:/icon/icon/选中圆.png);image: url(:/icon/icon/minganci.png);")
        elif index == 3:
            # self.ui.home_top_title.setText("系统设置")
            self.reset_menu_style()
            self.ui.setup_but.setStyleSheet("background-image: url(:/icon/icon/选中圆.png);image: url(:/icon/icon/设置.png);")
        else:
            # self.ui.home_top_title.setText("个人中心")
            self.reset_menu_style()
            self.ui.my_but.setStyleSheet("background-image: url(:/icon/icon/选中圆.png);image: url(:/icon/icon/我的.png);")

    # 连接千牛
    def connectqianniu(self):
        """直接查找并连接千牛接待台窗口"""
        self.append_log_message("开始查找千牛接待台窗口...")
        
        # 第一步：查找主窗口
        parent_hwnd = win32gui.FindWindow("Qt5152QWindowIcon", "千牛接待台")
        
        if not parent_hwnd:
            self.append_log_message("未找到接待台主窗口，尝试启动千牛...")
            # 启动千牛主程序
            os.startfile("aliim:login")
            time.sleep(5)  # 等待启动
            
            # 再次尝试查找
            parent_hwnd = win32gui.FindWindow("Qt5152QWindowIcon", "千牛接待台")
            if not parent_hwnd:
                self.append_log_message("启动千牛后仍找不到接待台窗口")
                return False
        
        self.append_log_message(f"找到接待台主窗口，句柄: 0x{parent_hwnd:X}")
        
        # 第二步：激活窗口
        try:
            # 还原窗口（如果最小化）
            win32gui.ShowWindow(parent_hwnd, win32con.SW_RESTORE)
            
            # 置顶窗口
            win32gui.SetForegroundWindow(parent_hwnd)
            time.sleep(0.5)
            
            self.append_log_message("窗口已激活并置顶")
        except Exception as e:
            self.append_log_message(f"激活窗口错误: {str(e)}")
        
        # 第三步：查找工作台子窗口
        child_hwnd = self.find_child_window(parent_hwnd, "千牛工作台", 3)
        
        if not child_hwnd:
            self.append_log_message("未找到工作台子窗口")
            return False
        
        self.append_log_message(f"找到工作台子窗口，句柄: 0x{child_hwnd:X}")
        
        # 第四步：刷新页面（确保注入JS）
        try:
            # 获取窗口位置
            rect = win32gui.GetWindowRect(child_hwnd)
            
            # 计算中心点
            center_x = rect[0] + (rect[2] - rect[0]) // 2
            center_y = rect[1] + (rect[3] - rect[1]) // 2
            
            # 点击窗口中心确保焦点
            pyautogui.click(center_x, center_y)
            time.sleep(0.5)
            
            # 发送多次F5刷新
            for i in range(3):
                win32gui.PostMessage(child_hwnd, win32con.WM_KEYDOWN, win32con.VK_F5, 0)
                win32gui.PostMessage(child_hwnd, win32con.WM_KEYUP, win32con.VK_F5, 0)
                time.sleep(1)
                self.append_log_message(f"发送刷新指令 ({i+1}/3)")
            
            self.append_log_message("刷新完成，等待注入JS")
            return True
        
        except Exception as e:
            self.append_log_message(f"刷新操作错误: {str(e)}")
            return False
    
    
    # 避免发送失败事件
    def avoid_send_failure(self):
        while True:
            class_name = "Qt5152QWindowIcon"
            title_substring = "服务态度提醒"
            windows = self.find_window(class_name, title_substring)
            if windows:
                hwnd = windows[0]
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)  # 还原窗口
                win32gui.SetForegroundWindow(hwnd)  # 激活窗口
                time.sleep(0.5)  # 等待窗口激活

                # 计算相对位置并点击
                self.doClick(hwnd,290,200)
                # pyautogui.click(x, y)
                time.sleep(0.5)
                # 点击回车 
                pyautogui.press('enter')

    def find_child_window(self, parent_handle, window_title, max_depth=3):
        """
        递归查找包含特定标题的子窗口
        :param parent_handle: 父窗口句柄
        :param window_title: 要查找的窗口标题
        :param max_depth: 最大递归深度
        :return: 窗口句柄或None
        """
        def callback(hwnd, hwnd_list):
            if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                hwnd_list.append(hwnd)
            return True
        
        # 当前层级查找
        hwnd_list = []
        try:
            win32gui.EnumChildWindows(parent_handle, callback, hwnd_list)
        except Exception as e:
            self.append_log_message(f"枚举子窗口错误: {str(e)}")
            return None
        
        # 在当前层级查找匹配的窗口
        for hwnd in hwnd_list:
            try:
                if win32gui.GetWindowText(hwnd) == window_title:
                    return hwnd
            except:
                continue
        
        # 递归查找（如果还有深度）
        if max_depth > 1:
            for hwnd in hwnd_list:
                result = self.find_child_window(hwnd, window_title, max_depth - 1)
                if result:
                    return result
        
        return None

    # 查找窗口
    def find_window(self,class_name, title):
        def enum_windows(hwnd, results):
            if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                if win32gui.GetClassName(hwnd) == class_name and title in win32gui.GetWindowText(hwnd):
                    results.append(hwnd)

        hwnds = []
        win32gui.EnumWindows(lambda hwnd, _: enum_windows(hwnd, hwnds), None)
        return hwnds

    # 检测右下角窗口是否存在
    def check_bottom_window(self):
        pass

    # 获取商品的说明书列表
    def get_goods_list(self):
        self.listWidget.clear()
        self.listWidget2.clear()
        self.goodsList = self.db.get_goodslist()
        weinub = 0
        if self.goodsList:
            for item in self.goodsList:
                # 根据type字段判断是否是已完善的商品
                if item['type'] == 1:
                    self.listWidget.addItem(item['product_name'])
                else:
                    self.listWidget2.addItem(item['product_name'])
                    weinub = weinub + 1
            if weinub == 0:
                self.listWidget2.addItem("用户询问的商品完善完啦~")
        else:
            self.listWidget.addItem("暂无数据,请点击下方添加按钮添加")
        
    @Slot(QModelIndex)
    def on_item_clicked(self, index):
        # 获取被点击的项的文本
        item = self.listWidget.itemFromIndex(index)
        type = 1
        if item is None:
            type = 0
            item = self.listWidget2.itemFromIndex(index)
        # 判断是否有这个商品
        if not any(item.text() == good['product_name'] for good in self.goodsList):
            self.show_error_message("没有该商品")
            return
        # 判断商品item商品名在goodsList的下标
        goodsindex = next(i for i, good in enumerate(self.goodsList) if good['product_name'] == item.text())

        self.add_new_goods(self.goodsList[goodsindex]['id'],type=type)

    # 为配合 Qt 的 connectSlotsByName 自动连接，补充具名槽函数，消除警告
    @Slot(QModelIndex)
    def on_listView_clicked(self, index):
        self.on_item_clicked(index)

    @Slot(QModelIndex)
    def on_listView2_clicked(self, index):
        self.on_item_clicked(index)

    # 退出登录
    def logout(self, event):
        # 清掉自动登录、token
        # self.db.update_system_info(auto_login=0)
        # self.db.update_system_info(token="")
        QMessageBox.information(self, "提示", "已退出登录")
        self.close()


    # 添加商品说明书
    def add_new_goods(self, goodsid=None,type=1):
        from src.newgoods import NewGoods
        
        self.newgoods = NewGoods(self.db, goodsid,type)
        self.newgoods.goodsAdded.connect(self.get_goods_list)
        self.newgoods.show()

    # 保存系统设置
    def updata_hosts(self):
        # 获取所有配置项
        role_description = self.ui.tishici.toPlainText()
        general_role_description = self.ui.tishici2.toPlainText()
        shop_description = self.ui.shop_description.toPlainText()
        ai_reply_style = self.ui.ai_reply_style.toPlainText()
        
        # 更新配置
        self.config["role_description"] = role_description
        self.config["general_role_description"] = general_role_description
        self.config["shop_description"] = shop_description
        self.config["ai_reply_style"] = ai_reply_style
        
        # 保存配置到文件
        self.save_config()
        QMessageBox.critical(self, "成功", '保存成功')

    # 弹出错误信息
    def show_error_message(self, message):
        # 显示错误消息
        QMessageBox.critical(self, "错误", message)

    # 开启flask服务
    # HomeWindow.run_flask
    def run_flask(self):
        global flask_app
        flask_app = FlaskApp(userinfo={"vip": 1})
        flask_app.run()


    # 开启websocket服务
    def run_websocket(self):
        global ws_server
        ws_server = WebSocketServer(self.dispatcher, self.ui)
        ws_server.run()

    # 执行发送消息
    def sendMassage(self):
        # 查找千牛接待台窗口
        hWnd = win32gui.FindWindowEx(0, 0, "Qt5152QWindowIcon", "千牛接待台")
        if not hWnd:
            print("未找到千牛接待台窗口")
            return False
        # 获取当前焦点窗口
        current_focus = win32gui.GetForegroundWindow()
        # 如果窗口最小化，恢复窗口
        if win32gui.IsIconic(hWnd):
            win32gui.ShowWindow(hWnd, win32con.SW_RESTORE)
        # 尝试将焦点设置到千牛窗口
        try:
            # 获取当前线程和目标窗口线程
            current_thread = win32api.GetCurrentThreadId()
            target_thread = win32process.GetWindowThreadProcessId(hWnd)[0]
            # 附加线程输入状态
            win32process.AttachThreadInput(current_thread, target_thread, True)
            # 将窗口带到前台
            win32gui.SetForegroundWindow(hWnd)
            # 确保窗口可见
            win32gui.ShowWindow(hWnd, win32con.SW_SHOW)
            
            # 给窗口设置焦点
            win32gui.SetFocus(hWnd)
            
            # 解除线程输入状态附加
            win32process.AttachThreadInput(current_thread, target_thread, False)
            
            # 等待窗口获得焦点
            time.sleep(0.1)
            
            # 检查窗口是否真的获得了焦点
            if win32gui.GetForegroundWindow() == hWnd:
                # 使用 win32api 发送回车键
                print('发送回车键')
                win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)  # 按下
                time.sleep(0.05)
                win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)  # 释放
                return True
            else:
                print("无法获取窗口焦点")
                return False
                
        except Exception as e:
            print(f"发送消息时出错: {str(e)}")
            return False
        # finally:
        #     # 如果之前有其他窗口在前台，尝试恢复
        #     if current_focus and current_focus != hWnd:
        #         try:
        #             win32gui.SetForegroundWindow(current_focus)
        #         except:
        #             pass

    def message_processor(self):
        while self.is_running:
            try:
                # 从队列获取消息，设置超时以便能够响应关闭信号
                message = self.message_queue.get(timeout=1)
                if message is None:
                    continue
                    
                try:
                    processed_data = self.process_data(message)
                    if processed_data is not None:
                        self.send_to_client(processed_data)
                except Exception as e:
                    print(f"处理或发送消息时出错: {str(e)}")
                    _write_crash_log('BUS', f"message_processor inner: {e}")
                finally:
                    self.message_queue.task_done()
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"消息处理器出错: {str(e)}")
                _write_crash_log('BUS', f"message_processor outer: {e}")
                continue

    def on_message_received(self, message):
        try:
            messages = json.loads(message)
            if json.loads(messages['message']) == 'send':
                self.sendMassage()
            else:
                # 将消息放入队列而不是直接创建新线程
                self.message_queue.put(messages)
                
        except KeyboardInterrupt:
            # 避免误触 Ctrl+C 等触发应用整体退出
            print("捕获到 KeyboardInterrupt，已忽略以保持服务运行。")
        except Exception as e:
            print(f"接收消息时出错: {str(e)}")

    # 模拟点击
    def doClick(self,hwnd, cx, cy):
        Long_position = win32api.MAKELONG(cx, cy)
        win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, Long_position)
        time.sleep(0.1)
        win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, Long_position)
   
    # 处理消息
    def process_data(self, message_data):
        # 获取客户端ID
        M = Message(self.db, self.ui, kb_client=self.kb_client)
        client_id = message_data['client_id']
        # 将消息内容从JSON字符串解析为字典
        message_data = json.loads(message_data['message'])
        if message_data['direction']:
            M.save_chatlog(message_data)
        else:
            # 接收并处理消息
            cent = self.loadInformation(message_data)
            M.save_chatlog(message_data)
            # 敏感词替换
            if cent is not None:
                for word, replacement in self.minganciDatakv.items():
                    cent = cent.replace(word, replacement)
                client_object = message_data['fromid']['nick']
                # 获取发送方账号昵称
                account = message_data['toid']['nick']
                if client_object == '' or account == '':
                    return None
                if message_data['loginid']['nick'] == message_data['fromid']['nick']:
                    return None
                url_protocol = f'aliim:sendmsg?touid=cntaobao{client_object}&uid=cntaobao{account}'
                # 打开连接
                webbrowser.open(url_protocol)
                print(url_protocol,'打开连接')
                data = {
                    'client_id': client_id,
                    'user': client_object,
                    'msg': cent,
                    'url': url_protocol
                }
                return data
            else:
                return None

    # 本地信息处理
    def loadInformation(self, message_data):
        M = Message(self.db,self.ui)
        ccode = message_data.get('ccode')
        # 获取会话信息
        chatinfo = self.db.get_association(message_data)
        # 判断会话是否绑定商品
        # 判断chatinfo['goodsinfo']是否纯在，如果存在，则赋值给goodsinfo变量
        if chatinfo and 'goodsinfo' in chatinfo:
            goodsinfo = chatinfo['goodsinfo']
        else:
            goodsinfo = None

        try:
            msg_type = message_data['originalData'].get('msgtype')
            template_id = message_data['templateId']
            # 辅助函数用于构建数据字典
            def build_data(goodsinfo=goodsinfo, **kwargs):
                base_data = {
                    "goodsinfo": goodsinfo,
                    "userid": message_data['fromid']['targetId'],
                    "username": message_data['fromid']['nick'],
                    "havMainId": message_data['loginid']['havMainId'],
                    "kefuid": message_data['toid']['targetId'],
                    "kefuname": message_data['toid']['nick'],
                    "goodsname": message_data['originalData']['goodsname'],
                    "url":message_data['originalData']['url'],
                    "ccode": ccode,
                }
                base_data.update(kwargs)
                return base_data
            if template_id == 101:  # 文字消息
                if msg_type == 'sysmsg':
                    return M.sysmessage()
                elif msg_type == 'text':
                    data = build_data(message=message_data['originalData']['message'])
                    return M.textmessage(data)
                elif msg_type == 'link':
                    urlinfo = json.loads(message_data['originalData']['urlinfo'])
                    data = build_data(goodsname=urlinfo['title'])
                    return M.linkmessage(data)
                elif msg_type == 'face':
                    return M.facemessage(message_data['originalData']['message'])
                elif msg_type == 'urllink':
                    data = build_data(message=message_data['originalData']['message'])
                    return M.urllinkmessage(data)
            elif template_id == 332001:                                                                 # 通过链接进入消息界面
                data = build_data(goodsname=message_data['originalData']['goodsname'],url=message_data['originalData']['url'])
                return M.linkmessage(data)
            elif template_id == 129:                                                                    # 发送带有规格信息的产品链接
                data = build_data(itemSku=message_data['originalData']['itemSku'], goodsname=message_data['originalData']['goodsname'])
                return M.linkmessage(data)

        except KeyError as e:
            print(f"Missing key in message_data - {e}")
            return None

        except Exception as e:
            print(f"出错了: {e}")
            return None

    # 将处理过的数据加入到队列
    def add_to_queue(self, processed_data, client_queue):
        client_queue.put(processed_data)

    # 线程工作函数，用于处理数据并加入队列
    def thread_worker(self, data):
        processed_data = self.process_data(data)
        if processed_data is not None:
            self.send_to_client(processed_data)
    # 向客户端发送数据
    def send_to_client(self, data):
        # 这里实现发送数据的逻辑
        ws_server.send_message(data['client_id'], json.dumps(data))
        self.sendMassage();

    # 关键词：添加关键词列表数据
    def populate_table(self, table):
        if self.keywords is not None:
            table.setRowCount(len(self.keywords))
            row = 0
            if len(self.keywords) > 0:
                for item in self.keywords:
                    table.setItem(row, 0, QTableWidgetItem(item['key']))
                    table.setItem(row, 1, QTableWidgetItem(item['value']))
                    row += 1

    # 关键词：显示右键菜单
    def showContextMenu(self, pos, table):
        contextMenu = QMenu(self)
        deleteAction = QAction("删除选中", self)
        deleteAction.triggered.connect(lambda: self.deleteItem(table))
        contextMenu.addAction(deleteAction)
        contextMenu.exec(table.mapToGlobal(pos))

    # 关键词：删除选中项
    def deleteItem(self, table):
        index = table.currentRow()
        data = self.keywords[index]
        if index >= 0:
            self.db.delete_keyword(data['id'])
            del self.keywordskv[data['key']]
            table.removeRow(index)

    # 关键词：修改选中项
    def item_changed(self, item):
        row = item.row()
        data = self.keywords[row]
        key_item = self.keyword_table.item(row, 0)
        value_item = self.keyword_table.item(row, 1)
        if key_item.text() != data['key'] or value_item.text() != data['value']:
            self.db.update_keyword(
                data['id'], key_item.text(), value_item.text())
            self.keywordskv[key_item.text()] = value_item.text()
            del self.keywordskv[data['key']]
            self.keywords[row] = self.db.getkeyword(data['id'])

    # 关键词：添加新关键词
    def add_new_keyword(self):
        new_key = self.ui.new_key_edit.text().strip()
        new_value = self.ui.new_value_edit.text().strip()
        if new_key and new_value:
            if new_key in self.keywordskv or new_key in self.minganciDatakv:
                QMessageBox.warning(self, "重复关键词", f"这个关键词'{new_key}'已经添加过了.")

            else:
                # 添加并更新关键词列表
                if self.keyword_table.rowCount() == 0:
                    self.keywords = []
                    self.keywords.append(self.db.add_keyword(
                        new_key, new_value, type=1))
                else:
                    self.keywords.append(self.db.add_keyword(
                        new_key, new_value, type=1))
                self.keywordskv[new_key] = new_value
                row_position = self.keyword_table.rowCount()
                self.keyword_table.insertRow(row_position)
                self.keyword_table.setItem(
                    row_position, 0, QTableWidgetItem(new_key))
                self.keyword_table.setItem(
                    row_position, 1, QTableWidgetItem(new_value))
                self.ui.new_key_edit.clear()
                self.ui.new_value_edit.clear()
        else:
            QMessageBox.warning(self, "缺少输入", "请输入关键词和出发内容.")

    # 敏感词：显示右键菜单
    def showContextMenuM(self, pos):
        contextMenu = QMenu(self)
        deleteAction = QAction("删除选中", self)
        deleteAction.triggered.connect(self.deleteItemc)
        contextMenu.addAction(deleteAction)
        contextMenu.exec(self.minganciTable.mapToGlobal(pos))

    # 敏感词：修改选中项
    def minganci_changed(self, item):
        row = item.row()
        data = self.minganciData[row]
        key_item = self.minganciTable.item(row, 0)
        value_item = self.minganciTable.item(row, 1)
        if key_item.text() != data['key'] or value_item.text() != data['value']:
            self.db.update_keyword(
                data['id'], key_item.text(), value_item.text())
            self.minganciDatakv[key_item.text()] = value_item.text()
            del self.minganciDatakv[data['key']]
            self.minganciData[row] = self.db.getkeyword(data['id'])

    # 敏感词：删除选中项
    def deleteItemc(self):
        index = self.minganciTable.currentRow()
        data = self.minganciData[index]
        if index >= 0:
            self.db.delete_keyword(data['id'])
            del self.minganciDatakv[data['key']]
            self.minganciTable.removeRow(index)

    # 敏感词：添加敏感词
    def add_new_sensitive(self):
        new_key = self.ui.minganci.text().strip()
        new_value = self.ui.tihuan.text().strip()

        if new_key and new_value:
            if new_key in self.keywordskv or new_key in self.minganciDatakv:
                QMessageBox.warning(self, "重复关键词", f"这个关键词'{new_key}'已经添加过了.")
            else:
                if self.minganciTable.rowCount() == 0:
                    self.minganciData = []

                self.minganciData.append(
                    self.db.add_keyword(new_key, new_value, type=2))

                self.minganciDatakv[new_key] = new_value
                row_position = self.minganciTable.rowCount()
                self.minganciTable.insertRow(row_position)
                self.minganciTable.setItem(
                    row_position, 0, QTableWidgetItem(new_key))
                self.minganciTable.setItem(
                    row_position, 1, QTableWidgetItem(new_value))

                self.ui.minganci.clear()
                self.ui.tihuan.clear()
        else:
            QMessageBox.warning(self, "缺少输入", "请输入关键词和出发内容.")

    # 敏感词：输出表格
    def populate_tablea(self):
        if self.minganciData is not None:
            self.minganciTable.setRowCount(len(self.minganciData))
            row = 0
            for key, value in self.minganciDatakv.items():
                self.minganciTable.setItem(row, 0, QTableWidgetItem(key))
                self.minganciTable.setItem(row, 1, QTableWidgetItem(value))
                row += 1

    # 输出添加首页日志
    def append_log_message(self, message):
        self.ui.textEdit.append(f"{message}")
    # 放进 HomeWindow 类里（与其它方法同级）
    def _ensure_kb(self):
        if not hasattr(self, "kb_client") or self.kb_client is None:
            self.kb_client = KBClient(base_url="http://127.0.0.1:38999")

            # 开发态：不拉起 exe；只创建 client
            self.kb_mgr = None

            # 兼容旧代码
            self.kb = self.kb_client

            # 可选：提示健康状态
            QtCore.QTimer.singleShot(1500, lambda: self.append_log_message(
                f"KB健康：{self.kb_client.health()}"
            ))


    def rebuild_knowledge_index(self):
        """点击按钮 → 触发 KB 引擎构建（有变化才重建）"""
        from PySide6.QtWidgets import QMessageBox
        self._ensure_kb()
        try:
            resp = self.kb_client.build(kb_dir=None, force_full=False)
            self.append_log_message(f"知识库索引：{resp}")
            QMessageBox.information(self, "成功",
                                    f"索引{resp.get('msg')}，片段数：{resp.get('size')}")
        except Exception as e:
            self.append_log_message(f"/build 调用失败：{e}")
            QMessageBox.critical(self, "错误", f"/build 调用失败：{e}")

    def add_knowledge_file(self):
        """选择文本文件 → 读取内容 → 直接发送到 KB 服务保存并索引（无需知道磁盘目录）"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        import os

        self._ensure_kb()
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择知识库文件", "", "文本文件 (*.txt *.md);;所有文件 (*)"
        )
        if not paths:
            return

        ok, fail = 0, 0
        for p in paths:
            try:
                # 读文件（含 GBK 兜底）
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        content = f.read()
                except UnicodeDecodeError:
                    with open(p, "r", encoding="gb18030", errors="ignore") as f:
                        content = f.read()

                # 发送给服务端保存并索引；rebuild=False=快速追加
                resp = self.kb_client.add_file(filename=os.path.basename(p),
                                            content=content,
                                            rebuild=False)
                mode = resp.get("mode")
                if mode == "append":
                    self.append_log_message(f"已追加：{os.path.basename(p)} → 新增 {resp.get('added')} 段 / 总 {resp.get('size')}")
                else:
                    self.append_log_message(f"已保存并重建：{os.path.basename(p)} → {resp}")
                ok += 1
            except Exception as e:
                fail += 1
                self.append_log_message(f"上传失败 {p}: {e}")

        if ok:
            QMessageBox.information(self, "成功", f"已处理 {ok} 个文件，失败 {fail} 个")
        elif fail:
            QMessageBox.critical(self, "错误", f"全部失败：{fail} 个")


    def add_knowledge_file_to_engine_dir(self):
        """把文件复制到 KB 引擎的 kb_dir，然后触发 /build（简化增量/全量重建）"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        import os, shutil, sys
        self._ensure_kb()
        # 1) 找到 kb_engine 根目录
        engine_dir = None
        try:
            # KBServiceManager 有 _find_engine；如果你不想用私有方法，可以在 kb_client 里加一个 get_engine_root()
            exe, engine_cwd = self.kb_mgr._find_engine()  # 返回 (exe路径, 工作目录)
            engine_dir = os.path.dirname(exe)
        except Exception:
            # 兜底：按发布布局推断
            if getattr(sys, "frozen", False):
                engine_dir = os.path.join(os.path.dirname(sys.executable), "kb_engine")
            else:
                engine_dir = os.path.abspath("kb_engine")

        kb_dir = os.path.join(engine_dir, "resources", "knowledge_data")
        os.makedirs(kb_dir, exist_ok=True)

        # 2) 选择文件并拷贝
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择知识库文件", "", "文本文件 (*.txt *.md);;所有文件 (*)"
        )
        if not paths:
            return

        copied = 0
        for p in paths:
            try:
                dst = os.path.join(kb_dir, os.path.basename(p))
                shutil.copy2(p, dst)
                copied += 1
                self.append_log_message(f"已复制到引擎目录：{dst}")
            except Exception as e:
                self.append_log_message(f"复制失败 {p}: {e}")

        if copied == 0:
            QMessageBox.warning(self, "提示", "没有文件被复制")
            return

        # 3) 触发构建（服务会做"有变化才重建"的判断）
        try:
            resp = self.kb_client.build(kb_dir=None, force_full=False)
            self.append_log_message(f"KB 构建：{resp}")
            QMessageBox.information(self, "成功", f"索引{resp.get('msg')}，片段数：{resp.get('size')}")
        except Exception as e:
            self.append_log_message(f"/build 调用失败：{e}")
            QMessageBox.critical(self, "错误", f"构建失败：{e}")

    def open_product_knowledge_manager(self):
        """打开商品知识库管理器"""
        try:
            from src.knowledge_manager import KnowledgeManager
            self.knowledge_manager = KnowledgeManager(self.db)
            self.knowledge_manager.show()
        except Exception as e:
            self.append_log_message(f"打开知识库管理器失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"打开知识库管理器失败: {str(e)}")



    # 页面拖动方法
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.isMaximized() == False:
            self.m_flag = True
            self.m_Position = event.globalPos() - self.pos()  # 获取鼠标相对窗口的位置
            event.accept()
            self.setCursor(QtGui.QCursor(QtCore.Qt.OpenHandCursor))  # 更改鼠标图标

    # 页面拖动方法
    def mouseMoveEvent(self, mouse_event):
        if QtCore.Qt.LeftButton and self.m_flag:
            self.move(mouse_event.globalPos() - self.m_Position)  # 更改窗口位置
            mouse_event.accept()

    # 页面拖动方法
    def mouseReleaseEvent(self, mouse_event):
        self.m_flag = False
        self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

    # 关闭程序时关闭所有服务器
    def closeEvent(self, event):
        # 设置关闭标志
        self.is_running = False
        # 等待所有消息处理完成
        self.message_queue.join()
        # 清理工作线程
        for _ in self.worker_threads:
            self.message_queue.put(None)  # 发送终止信号
        for worker in self.worker_threads:
            worker.join(timeout=1)
            
        # 关闭其他服务（放入 try，避免关闭异常导致崩溃）
        try:
            if ws_server:
                print("正在关闭 WebSocket 服务器...")
                ws_server.stop_server()
        except Exception as e:
            print(f"关闭 WebSocket 失败: {e}")
        try:
            if flask_app:
                flask_app.shutdown()
        except Exception as e:
            print(f"关闭 Flask 失败: {e}")

        print("所有服务器已关闭，程序退出。")
        if event:
            event.accept()
            super().closeEvent(event)
        try:
            if hasattr(self, "kb_mgr") and self.kb_mgr:
                self.kb_mgr.stop()
        except Exception as e:
            print(f"关闭 KB 引擎失败: {e}")

# 检测版本更新
def check_for_updates():
    try:
        r = requests.get(f"{AUTH_BASE}/health", timeout=3)
        return True if r.status_code == 200 else True  # 一律允许进入登录
    except Exception:
        return True

if __name__ == '__main__':
    # 安装全局异常/Qt消息处理，避免异常导致崩溃并记录日志
    sys.excepthook = _excepthook
    try:
        threading.excepthook = _thread_excepthook
    except Exception:
        pass
    _enable_faulthandler()
    atexit.register(_disable_faulthandler)
    try:
        from PySide6.QtCore import qInstallMessageHandler
        qInstallMessageHandler(_qt_message_handler)
    except Exception:
        pass

    # DPI 设置必须在 QApplication 创建前调用
    try:
        QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
        QApplication.setHighDpiScaleFactorRoundingPolicy(QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    except Exception:
        pass

    db_manager = DatabaseManager()
    # system_info = db_manager.get_system_info()      # 本地系统缓存信息
    app = QApplication(sys.argv)
    # 首先弹出启动画面
    # 在显示    窗口之前，检查版本更新
    if check_for_updates():
        login = LoginWindow()
        login.show()
    else:
        updata = Updata(current_version)
        updata.show()
    sys.exit(app.exec())
