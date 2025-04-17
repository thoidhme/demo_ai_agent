import re
import json
from typing import List
from tools.rag import DBCollector


class RoutineResponse(object):
    def __init__(self, response_data: str = "",  response_rule: str = None):
        self.response_rule = response_rule
        self.response_data = response_data

    def generate_prompt(self, system_message: str):
        return system_message % (json.dumps(self.response_data), self.response_rule or "")


class MissingContextException(Exception):
    def __init__(self, collector: DBCollector = DBCollector()):
        self.collector = collector

class NeedMoreInfoException(Exception):
    def __init__(self, collector: DBCollector = DBCollector()):
        self.collector = collector


def extract_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).replace("\n","").strip()
    start = text.find('{')
    if start == -1:
        return {}

    brace_count = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                json_str = text[start:i+1]
                try:
                    return json.loads(json_str.replace("\n", ""))
                except json.JSONDecodeError:
                    continue
    return {}
