# message.py
from datetime import datetime
import os
import random
import requests
import pygame
import json
from typing import List, Tuple, Optional, Dict

from thefuzz import process, fuzz
from .knowledge_service.client import LocalRetrieverProxy  # 微服务客户端
# from zhipuai import ZhipuAI  # 如果你要切到智谱，可以自己替换 _call_llm
# message.py
DEBUG = True

def dlog(*args):
    if DEBUG:
        print("[RAG-DEBUG]", *args)

class Message:
    """
    客户端本地RAG版：
    1) 关键词命中 -> 直接回复
    2) 未命中 -> 本地向量检索（知识库）
    3) 有上下文 -> 调一次云端LLM生成（DeepSeek/可替换）
    4) 无上下文 -> 返回“请稍等”
    """
    def __init__(self, db, ui=None):
        self.db = db
        self.ui = ui

        # 文案参数
        self.prompt_rule = (
            "你是专业电商客服。优先依据下面【知识】回答用户问题；"
            "若【知识】没有覆盖，请基于常识给出简明、安全的回答，并标注需要进一步核实。\n\n【知识】\n{context}"
        )

        # 匹配度（关键词容忍阈值）
        self.pipeidu = 75

        # 本地向量检索器（离线加载）
        # 模型维度按你的模型改：bge-small-zh-v1.5 是 768 维
        self.retriever = LocalRetrieverProxy(
            model_dir="src/models/bge-small-zh-v1.5", 
            index_dir="src/knowledge_base/rag_index",
            dim=768
        )

        # 云端LLM配置（可换成你自己的服务）
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
            # 注意：此处不直接操作 UI，避免非主线程更新导致崩溃
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

        # 先店铺级
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

    # ====== 本地向量检索 ======
    def _retrieve_local_context(self, query: str, top_k: int = 3) -> str:
        try:
            results = self.retriever.search(query, top_k=top_k)  # List[(text, score)]
            # hnswlib 用 cosine 距离，值越小越相近；这里只拼文本
            ctx = "\n\n".join([seg for seg, _ in results if seg])
            return ctx.strip()
        except Exception:
            return ""

    # ====== 云端LLM 生成 ======
    def _call_llm(self, user_query: str, context: str, ccode: Optional[str] = None) -> str:
        """默认走 DeepSeek，可自行替换为你的服务端"""
        if not self.llm_key:
            # 无密钥时，尽量用检索到的文本给出直出式回答（不经过LLM）
            if context:
                snippet = context.strip().split("\n\n")[0][:200]
                return f"根据已知资料：{snippet}……（如需更详细回复请稍等）"
            return "您好，正在为您查询相关信息，请稍等片刻。"

        sys_prompt = self.prompt_rule.format(context=context or "")
        # 汇入会话历史（最多近 6 条）
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
            # LLM 失败时的兜底：返回检索片段，避免总是“请稍等”
            if context:
                snippet = context.strip().split("\n\n")[0][:200]
                return f"参考资料显示：{snippet}……（如需进一步确认请稍等）"
            return "抱歉，当前网络繁忙，我稍后继续为您确认。"

    # ====== 文本消息主逻辑（客户端本地RAG） ======
    def textmessage(self, data: dict) -> Optional[str]:
        """
        data:
          - message: str
          - username: str
          - goodsinfo: Optional[dict]  (可能包含 details, id ...)
          - ccode: str (会话ID)
        """
        msg = data.get("message", "") or ""
        if not msg.strip():
            return None

        username = data.get("username", "unknown")
        goodsinfo = data.get("goodsinfo")  # 可能为 None
        ccode = data.get("ccode")

        # 1) 关键词命中
        store_id = goodsinfo.get('id') if goodsinfo else None
        kw_hit = self._match_keywords(msg, store_id=store_id)
        if kw_hit:
            reply = self.add_emoji(kw_hit)
            self.local_save_chatlog(username, msg, reply, "关键词匹配")
            return reply

        # 2) 构造知识上下文：优先使用商品说明书 details；否则用本地向量检索
        #    （你希望“没有说明书就不要乱答”，所以如果两者都没有，直接“请稍等”）
        context_parts: List[str] = []

        # 商品说明书
        if goodsinfo and goodsinfo.get("details"):
            context_parts.append(str(goodsinfo["details"]).strip())

        # 本地向量检索
        # 注：即使有 details，也可以把检索到的补充在后面，一起给模型，召回更稳
        local_ctx = self._retrieve_local_context(msg, top_k=3)
        if local_ctx:
            context_parts.append(local_ctx)

        full_context = "\n\n".join([c for c in context_parts if c])

        # 3) 没有任何上下文 -> 直接尝试调用 LLM（允许常识回答），或给出友好占位
        if not full_context:
            self.play_sound()
            ans_noctx = self._call_llm(msg, "", ccode)
            self.local_save_chatlog(username, msg, ans_noctx, "AI(无知识兜底)")
            if ccode:
                Message.sessions.setdefault(ccode, []).extend([
                    {"role": "user", "content": msg},
                    {"role": "assistant", "content": ans_noctx},
                ])
            return ans_noctx

        # 4) 有上下文 -> 调一次云端LLM生成
        ans = self._call_llm(msg, full_context, ccode) or "请稍等"

        # 转人工提示（保持你的旧逻辑）
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
        return ans

    # ====== 其它类型消息（保持简化，可按需保留/删除） ======
    def facemessage(self, data: str) -> str:
        # 简单随机表情
        choices = ["/:-F","/:Y","/:809","/:087"]
        reply = random.choice(choices)
        self.local_save_chatlog("unknown", data, reply, "表情消息")
        return reply

    def urllinkmessage(self, data: dict) -> Optional[str]:
        # 这里保留你原来的业务分支（根据 product_id 建立关联等）
        # 如果还没实现后台，这里可以直接“请稍等”或仅做提示音
        self.play_sound()
        return None

    def linkmessage(self, data: dict) -> Optional[str]:
        self.play_sound()
        return None

    def save_chatlog(self, data: dict):
        # 如果你还在把原始聊天存后台，这里调用 self.db.save_chatlog(data)
        try:
            self.db.save_chatlog(data)
        except Exception:
            pass
