import re
import json


from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langchain.schema import BaseMessage
class Engine(object):
    api_base: str
    api_key: str

    def __init__(self, model: str, temp: float = 0.7):
        self.llm = ChatOpenAI(
            model=model,
            openai_api_key=self.api_key,
            openai_api_base=self.api_base,
            temperature=temp,
        )

    def invoke(self, message: MessagesState) -> BaseMessage:
        try:
            return self.llm.invoke(message)
        except Exception as ex:
            print(ex)
            return None


class GrogEngine(Engine):
    api_base = "https://api.groq.com/openai/v1"
    api_key = ""
