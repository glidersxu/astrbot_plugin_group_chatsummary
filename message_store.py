'''#author: 胖加菲
#date: 2025/4/9 15:05
#desc:
1-功能描述：

2-实现步骤：

'''
# !/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import pickle
from collections import deque
from datetime import datetime

class MessageStore:
    def __init__(self, filename: str, max_messages_per_target: int = 200):
        self.filename = filename
        self.max_messages_per_target = max_messages_per_target
        self.messages = self.load_messages()

    def load_messages(self):
        if os.path.exists(self.filename):
            with open(self.filename, "rb") as f:
                return pickle.load(f)
        return {}

    def save_messages(self):
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        with open(self.filename, "wb") as f:
            pickle.dump(self.messages, f)

    def add_message(self, target: str, is_private: bool, sender: str, content: str):
        if target not in self.messages:
            self.messages[target] = deque(maxlen=self.max_messages_per_target)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg_line = f\"[{timestamp}] {sender}: {content}\"
        self.messages[target].append(msg_line)
        self.save_messages()

    def get_messages(self, target: str, count: int):
        if target not in self.messages:
            return []
        messages = list(self.messages[target])[-count:]
        return messages
