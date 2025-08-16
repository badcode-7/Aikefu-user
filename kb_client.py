# kb_client.py
import os, sys, time, json, subprocess, threading, shutil
from pathlib import Path
import requests

DEFAULT_BASE = "http://127.0.0.1:38999"

def get_resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS  # PyInstaller _MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class KBClient:
    def __init__(self, base_url: str = DEFAULT_BASE, timeout: float = 6.0):
        self.base = base_url.rstrip("/")
        self.timeout = timeout

    def health(self):
        return requests.get(f"{self.base}/health", timeout=self.timeout, verify=False).json()

    def wait_until_ready(self, seconds: float = 25.0):
        deadline = time.time() + seconds
        last_err = None
        while time.time() < deadline:
            try:
                r = requests.get(f"{self.base}/health", timeout=1.5, verify=False)
                if r.ok and r.json().get("status") == "ok":
                    return True
            except Exception as e:
                last_err = e
            time.sleep(0.5)
        raise RuntimeError(f"KB engine not ready: {last_err}")

    def build(self, kb_dir: str | None = None, force_full: bool = False):
        payload = {"kb_dir": kb_dir, "force_full": force_full}
        r = requests.post(f"{self.base}/build", json=payload, timeout=max(self.timeout, 30), verify=False)
        r.raise_for_status()
        return r.json()

    def add_texts(self, texts: list[str]):
        r = requests.post(f"{self.base}/add_texts", json={"texts": texts}, timeout=max(self.timeout, 30), verify=False)
        r.raise_for_status()
        return r.json()

    def search(self, query: str, top_k: int = 3):
        r = requests.post(f"{self.base}/search", json={"query": query, "top_k": top_k}, timeout=max(self.timeout, 10), verify=False)
        r.raise_for_status()
        return r.json()

class KBServiceManager:
    """负责在本地启动/关闭 kb_engine.exe，并等待健康就绪。"""
    def __init__(self, client: KBClient, log_fn=None):
        self.client = client
        self.proc: subprocess.Popen | None = None
        self.log = log_fn or (lambda msg: print(msg))

    def _find_engine(self) -> tuple[str, str]:
        """
        返回 (exe路径, 工作目录). 你可以把 kb_engine 整个文件夹
        放在发布目录下，例如:
          dist/app/kb_engine/kb_engine.exe
        """
        candidates = [
            # onedir 建议路径
            get_resource_path(os.path.join("kb_engine", "kb_engine.exe")),
            # 同目录（开发态或你手动并排放）
            get_resource_path("kb_engine.exe"),
            # PATH 中可执行
            shutil.which("kb_engine") or "",
        ]
        for p in candidates:
            if p and os.path.exists(p):
                return p, os.path.dirname(p)
        raise FileNotFoundError("未找到 kb_engine 可执行文件，请确认它随包分发在 kb_engine/ 目录。")

    def start(self, cfg_path: str | None = None):
        exe, cwd = self._find_engine()
        env = os.environ.copy()
        if cfg_path:
            env["KB_CFG"] = cfg_path  # 指定 config.json（可选）

        creationflags = 0
        startupinfo = None
        if os.name == "nt":
            # 隐藏黑框（Windows）
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        self.log(f"[KB] 启动引擎：{exe}")
        self.proc = subprocess.Popen(
            [exe], cwd=cwd, env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            startupinfo=startupinfo, creationflags=creationflags
        )
        # 健康检查
        self.client.wait_until_ready(25.0)
        self.log("[KB] 引擎就绪")

    def start_async(self, cfg_path: str | None = None):
        def _run():
            try:
                self.start(cfg_path=cfg_path)
            except Exception as e:
                self.log(f"[KB] 启动失败：{e}")
        t = threading.Thread(target=_run, daemon=True)
        t.start()

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.log("[KB] 关闭引擎")
            try:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
            except Exception:
                pass
        self.proc = None
