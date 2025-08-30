# message.py  —— 仅依赖 KB 微服务；不再 import retriever/torch
from datetime import datetime
import os
import random
import requests
import pygame
import json
from typing import List, Optional, Dict, Any

from thefuzz import process, fuzz

# ★ 新增：使用微服务客户端
try:
    # 与 kb_client.py 位于同一项目内；若你把它放在 src/ 下，请按实际改导入路径
    from kb_client import KBClient
except Exception:
    KBClient = None  # 允许缺失，运行期再兜底报错

DEBUG = True
def dlog(*args):
    if DEBUG:
        print("[RAG-DEBUG]", *args)

class Message:
    """
    处理客服对话：
    1) 关键词命中 -> 直接回复
    2) 未命中 -> 调用 KB 微服务检索获得上下文
    3) 有上下文 -> 调一次云端 LLM 生成（可自换）
    4) 无上下文 -> 友好兜底
    """
    def __init__(self, db, ui: Optional[object] = None, kb_client: Optional["KBClient"] = None):
        self.db = db
        self.ui = ui

        # ★ 接入 KB 微服务（优先用传入的，其次用 ui.kb_client，最后自己构造一个）
        self.kb_client = kb_client or getattr(ui, "kb_client", None)
        if self.kb_client is None:
            if KBClient is None:
                raise RuntimeError("未找到 KBClient，请确保 kb_client.py 可导入，或在创建 Message 时传入 kb_client 实例。")
            base = os.getenv("KB_BASE", "http://127.0.0.1:38999")
            self.kb_client = KBClient(base_url=base)

        # 文案参数
        self.prompt_rule = (
            "你是专业电商客服。优先依据下面【知识】回答用户问题；"
            "若【知识】没有覆盖，请基于常识给出简明、安全的回答，并标注需要进一步核实。\n\n【知识】\n{context}"
        )

        # 关键词匹配阈值
        self.pipeidu = 75

        # 云端 LLM（示例：DeepSeek，可自换；建议用环境变量）
        self.llm_endpoint = os.getenv("DEESEEK_ENDPOINT", "https://api.deepseek.com/v1/chat/completions")
        # 为打包方便，显式写死 DeepSeek 密钥（注意：公开仓库请勿提交此密钥）
        self.llm_key = "sk-9f546130337e4fb893e089b1c2169cf5"
        # 会话记忆容器（按会话ID ccode 保存最近轮次）
        if not hasattr(Message, "sessions"):
            Message.sessions: Dict[str, List[Dict[str, str]]] = {}

    # ====== 公共小工具 ======
    def sysmessage(self):
        return None

    def add_emoji(self, text: str) -> str:
        emojis = ["/:809","/:^x^","/:814","/:066","/:071","/:081","/:-F","/:lip","/:Y","/:803","/:008","/:073","/:813"]
        if emojis:
            text += random.choice(emojis)
        return text

    def extract_keys(self, keyword_list):
        if not keyword_list:
            return {}
        return {k['key']: k['value'] for k in keyword_list}

    def play_sound(self):
        try:
            pygame.mixer.init()
            pygame.mixer.music.load('./static/1.mp3')
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except Exception:
            pass

    def local_save_chatlog(self, username, message, ai_reply, message_type):
        try:
            filename = f'./msglog/{datetime.now().date()}/{username}.txt'
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(f'【{message_type}】[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]顾客{username}: {message} 【处理结果】： {ai_reply}\n\n')
        except Exception:
            pass

    # ====== 关键词命中 ======
    def _match_keywords(self, text: str, store_id: Optional[int] = None) -> Optional[str]:
        # 全局关键词
        global_kws = self.extract_keys(self.db.get_keywords())
        # 店铺/商品级关键词
        store_kws = self.extract_keys(self.db.get_stoetkeywords(store_id)) if store_id else {}

        # 店铺优先
        if store_kws:
            m = process.extractOne(text, store_kws.keys(), scorer=fuzz.token_set_ratio)
            if m and m[1] > self.pipeidu:
                return store_kws[m[0]]

        # 再全局
        if global_kws:
            m = process.extractOne(text, global_kws.keys(), scorer=fuzz.token_set_ratio)
            if m and m[1] > self.pipeidu:
                return global_kws[m[0]]
        return None

    # ====== 通过微服务检索上下文（代替本地 retriever） ======
    def _retrieve_local_context(self, query: str, top_k: int = 3) -> str:
        try:
            resp = self.kb_client.search(query, top_k=top_k)  # 期望返回 {"results":[{"text":..., "score":...}, ...]}
            print("KB search response:", resp)  # 调试输出
            results = resp.get("results", [])
            # 兼容：若服务端返回 tuple/list，也能兜住
            def _to_text(hit: Any) -> str:
                if isinstance(hit, dict):
                    return str(hit.get("text", ""))
                if isinstance(hit, (list, tuple)) and hit:
                    return str(hit[0])
                return str(hit)
            ctx = "\n\n".join([_to_text(h) for h in results if _to_text(h)])
            return ctx.strip()
        except Exception as e:
            dlog("KB search failed:", e)
            return ""

    # ====== 云端 LLM 生成 ======
    def _call_llm(self, user_query: str, context: str, ccode: Optional[str] = None) -> str:
        # 无密钥：做一个不经 LLM 的友好兜底
        if not self.llm_key:
            if context:
                snippet = context.strip().split("\n\n")[0][:200]
                return f"根据已知资料：{snippet}……（如需更详细回复请稍等）"
            return "您好，正在为您查询相关信息，请稍等片刻。"

        sys_prompt = self.prompt_rule.format(context=context or "")
        history: List[Dict[str, str]] = []
        if ccode and Message.sessions.get(ccode):
            history = Message.sessions[ccode][-6:]

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": sys_prompt},
                *history,
                {"role": "user", "content": user_query}
            ],
            "temperature": 0.6,
            "max_tokens": 512,
            "top_p": 0.9
        }
        try:
            r = requests.post(
                self.llm_endpoint,
                json=payload,
                timeout=30,
                headers={
                    "Authorization": f"Bearer {self.llm_key}",
                    "Content-Type": "application/json"
                }
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            else:
                dlog("LLM HTTP", r.status_code, r.text[:200])
        except Exception as e:
            dlog("LLM ERROR", str(e))

        # LLM 失败兜底
        if context:
            snippet = context.strip().split("\n\n")[0][:200]
            return f"参考资料显示：{snippet}……（如需进一步确认请稍等）"
        return "抱歉，当前网络繁忙，我稍后继续为您确认。"

    # ====== 文本消息主逻辑 ======
    def textmessage(self, data: dict) -> Optional[str]:
        """
        data:
          - message: str
          - username: str
          - goodsinfo: Optional[dict]
          - ccode: str (会话ID)
        """
        msg = data.get("message", "") or ""
        if not msg.strip():
            return None

        username = data.get("username", "unknown")
        goodsinfo = data.get("goodsinfo")
        ccode = data.get("ccode")

        # 1) 关键词命中
        store_id = goodsinfo.get('id') if goodsinfo else None
        kw_hit = self._match_keywords(msg, store_id=store_id)
        if kw_hit:
            reply = self.add_emoji(kw_hit)
            
            # 敏感词替换（关键词匹配的回复也需要过滤）
            sensitive_words = self.db.get_sensitive()
            sensitive_dict = {item['key']: item['value'] for item in sensitive_words}
            for word, replacement in sensitive_dict.items():
                reply = reply.replace(word, replacement)
            
            self.local_save_chatlog(username, msg, reply, "关键词匹配")
            return reply

        # 2) 组织知识上下文（商品 details + KB 检索）
        context_parts: List[str] = []
        if goodsinfo and goodsinfo.get("details"):
            context_parts.append(str(goodsinfo["details"]).strip())

        local_ctx = self._retrieve_local_context(msg, top_k=3)
        if local_ctx:
            context_parts.append(local_ctx)

        full_context = "\n\n".join([c for c in context_parts if c])

        # 3) 无上下文 → 兜底
        if not full_context:
            self.play_sound()
            ans_noctx = self._call_llm(msg, "", ccode)
            
            # 敏感词替换（无上下文兜底回复也需要过滤）
            if ans_noctx is not None:
                sensitive_words = self.db.get_sensitive()
                sensitive_dict = {item['key']: item['value'] for item in sensitive_words}
                for word, replacement in sensitive_dict.items():
                    ans_noctx = ans_noctx.replace(word, replacement)
            
            self.local_save_chatlog(username, msg, ans_noctx, "AI(无知识兜底)")
            if ccode:
                Message.sessions.setdefault(ccode, []).extend([
                    {"role": "user", "content": msg},
                    {"role": "assistant", "content": ans_noctx},
                ])
            return ans_noctx

        # 4) 有上下文 → LLM 生成
        ans = self._call_llm(msg, full_context, ccode) or "请稍等"

        # 转人工提示
        if "转人工" in ans or ans.strip() == "转人工":
            self.play_sound()
            self.local_save_chatlog(username, msg, ans, "AI(转人工)")
            return None

        self.local_save_chatlog(username, msg, ans, "AI(本地RAG)")
        if ccode:
            Message.sessions.setdefault(ccode, []).extend([
                {"role": "user", "content": msg},
                {"role": "assistant", "content": ans},
            ])
        
        # 敏感词替换
        if ans is not None:
            sensitive_words = self.db.get_sensitive()
            sensitive_dict = {item['key']: item['value'] for item in sensitive_words}
            for word, replacement in sensitive_dict.items():
                ans = ans.replace(word, replacement)
        
        return ans

    # ====== 其它类型 ======
    def facemessage(self, data: str) -> str:
        choices = ["/:-F","/:Y","/:809","/:087"]
        reply = random.choice(choices)
        self.local_save_chatlog("unknown", data, reply, "表情消息")
        return reply

    def urllinkmessage(self, data: dict) -> Optional[str]:
        self.play_sound()
        return None

    def linkmessage(self, data: dict) -> Optional[str]:
        self.play_sound()
        return None

    def save_chatlog(self, data: dict):
        try:
            self.db.save_chatlog(data)
        except Exception:
            pass
