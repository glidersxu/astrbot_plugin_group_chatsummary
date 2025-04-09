'''#author: 胖加菲
#date: 2025/4/9 15:05
#desc:
1-功能描述：

2-实现步骤：

'''
# !/usr/bin/env python
# -*- coding:utf-8 -*-
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api.all import event_message_type, EventMessageType
from astrbot.api.message_components import *
import os
import json
from astrbot.api import logger
from data.plugins.astrbot_plugin_group_chatsummary.message_store import MessageStore

def with_project_path(file: str) -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), file)

@register("astrbot_plugin_group_chatsummary", "gliders", "群聊消息总结插件", "1.0.0")
class GroupChatSummaryPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.message_store = MessageStore(filename=with_project_path("message_store.data"))

    @filter.command("总结消息")
    async def summary(self, event: AstrMessageEvent, count: int = None):
        if not event.is_admin():
            event.stop_event()
            return
        if count is None:
            yield event.plain_result("未传入要总结的聊天记录数量\n请按照「 /消息总结 [数量]」示例：/消息总结 20")
            event.stop_event()
            return
        target = event.get_group_id() if event.get_group_id() != "" else event.get_sender_id()
        messages = self.message_store.get_messages(target, count)
        if not messages:
            yield event.plain_result("没有可总结的消息")
            event.stop_event()
            return
        logger.info(f"消息总结 target:{target}, count:{count}, sender:{event.get_sender_id()}")
        msg = "\n".join(messages)
        llm_response = await self.context.get_using_provider().text_chat(
            prompt=self.load_prompt(),
            contexts=[{"role": "user", "content": msg}],
        )
        yield event.plain_result(llm_response.completion_text)

    @filter.command("消息总结")
    async def summary_alias(self, event: AstrMessageEvent, count: int = None):
        async for result in self.summary(event, count):
            yield result

    @event_message_type(EventMessageType.ALL, priority=3)
    async def on_all_message(self, event: AstrMessageEvent):
        if event.get_platform_name() != "gewechat":
            return
        if event.get_self_id() == event.get_sender_id():
            return
        sender = event.get_sender_name() if event.get_group_id() != "" else event.get_sender_id()
        target = event.get_group_id() if event.get_group_id() != "" else event.get_sender_id()
        is_private = event.get_group_id() == ""
        content = event.message_obj.message_str
        msg_type = event.message_obj.raw_message.get('MsgType', 0)
        messages = event.get_messages()
        message = messages[0] if messages else None
        if msg_type == 1 and (content.startswith("总结消息") or content.startswith("消息总结")):
            event.should_call_llm(True)
            return
        if msg_type == 49 and isinstance(message, Reply):
            content = message.message_str
        if not content:
            return
        self.message_store.add_message(target, is_private, sender, content)

    def load_prompt(self):
        with open(os.path.join('data', 'config', 'astrbot_plugin_group_chatsummary_config.json'), 'r', encoding='utf-8-sig') as f:
            config = json.load(f)
            prompt_str = config.get('prompt', {})
            return str(prompt_str.replace('\\\\n', '\\n'))
