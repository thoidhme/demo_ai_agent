import json
import importlib
import re

from llm.prompt import SystemPrompt
from dataclasses import dataclass
from typing import List, Dict, Optional
from llm.engine import Engine
from langgraph.graph import StateGraph, MessagesState
from tools.utils import extract_json
from langgraph.checkpoint.memory import MemorySaver
from langchain.schema import HumanMessage, SystemMessage


@dataclass
class InCompleteInfo:
    message: Optional[str] = ""
    missing: Optional[List[str]] = None


@dataclass
class Routine:
    ready: bool
    routine: str
    description: str
    parameters: Optional[Dict[str, str]] = None
    incomplete: Optional[InCompleteInfo] = None
    # origin_input: Optional[str] = None


@dataclass
class PromptState:
    # Input from user
    user_input: Optional[str]
    conversation: Optional[MessagesState] = None
    next_step: Optional[str] = None
    thread_id: Optional[str] = None
    summary_context: Optional[str] = None
    rag_query_str: Optional[str] = None
    rag_query_results: Optional[List[str]] = None
    final_response: Optional[str] = None
    routine: Optional[Routine] = None
    response_data: Optional[str] = None


@dataclass
class Context:
    origin_input: Optional[str] = None
    routine: Optional[Routine] = None
    conversation: Optional[List[dict]] = None


class Orchestrator(object):
    def __init__(self, llm: Engine, rag_data: Dict = {}):
        self.llm = llm
        self.graph = None
        self.builder = None
        self.rag_data = rag_data
        self.context: Context = None

        builder = StateGraph(PromptState)

        builder.add_node("analyze_input", self.analyze_input)
        builder.add_node("generate_routine_query", self.generate_routine_query)
        builder.add_node("collect_missing_params", self.collect_missing_params)
        builder.add_node("retrieve_routine_data", self.retrieve_routine_data)
        builder.add_node("select_routine", self.select_routine)
        builder.add_node("call_routine", self.call_routine)
        builder.add_node("generate_response", self.generate_response)

        # Add edges
        builder.add_conditional_edges("analyze_input", lambda state: state.next_step)
        builder.add_edge("generate_routine_query", 'retrieve_routine_data')
        builder.add_edge("retrieve_routine_data", 'select_routine')
        builder.add_conditional_edges("collect_missing_params", lambda state: state.next_step)
        builder.add_conditional_edges("select_routine", lambda state: state.next_step)
        builder.add_edge("call_routine", 'generate_response')

        builder.set_entry_point("analyze_input")
        builder.set_finish_point("generate_response")

        memory = MemorySaver()

        self.builder = builder
        self.graph = builder.compile(checkpointer=memory)

    def clean_llm_output(self, text: str) -> str:
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        return text.strip()

    def analyze_input(self, state: PromptState) -> PromptState:
        # prior_context = ""
        # if self.context:
        #     prior_context = json.dumps(self.context.conversation or [])

        if not state.conversation:
            state.conversation = MessagesState(messages=[])

        human_message = HumanMessage(state.user_input)
        system_message = SystemMessage(SystemPrompt.input_message(""))
        messages = state.conversation["messages"] + \
            [system_message, human_message]
        state.conversation["messages"].append(human_message)

        response = self.llm.invoke(messages)

        json_data = extract_json(self.clean_llm_output(response.content))
        if not json_data:
            # TODO: handle exception
            return state

        state.next_step = json_data.get("action", None)

        if not state.next_step and not self.context:
            state.next_step = 'select_routine'
        elif not state.next_step:
            state.next_step = 'generate_response'

        return state

    def generate_routine_query(self, state: PromptState) -> PromptState:
        # reset context data if user begin with a new intent
        if self.context:
            self.context = None

        response = self.llm.invoke([
            SystemMessage(SystemPrompt.rag_query_message()),
            HumanMessage(state.user_input),
        ])
        json_data = extract_json(self.clean_llm_output(response.content))

        if not json_data:
            return state

        state.next_step = "retrieve_routine_data"
        state.rag_query_str = json_data.get("query", None) or ""

        return state

    def retrieve_routine_data(self, state: PromptState) -> PromptState:
        # Query data from rag database
        state.rag_query_results = self.rag_data["routine"].query(
            state.rag_query_str, k=3)

        state.next_step = "select_routine"

        return state

    def collect_missing_params(self, state: PromptState) -> PromptState:
        if not self.context:
            state.next_step = "select_routine"
            return state

        parameter_exists = json.dumps(
            [k for k, val in self.context.routine.parameters.items() if val])

        function_data = json.dumps(["%s, %s" % (
            self.context.routine.routine, self.context.routine.description)])

        prev_question = "".join([
            message.get("content") for message in self.context.conversation if message.get("role") == "bot"][-1:])

        human_message = HumanMessage(state.user_input)
        system_message = SystemMessage(SystemPrompt.collect_missing_params_message(function_data=function_data))
        messages = state.conversation["messages"] + \
            [system_message, human_message]

        response = self.llm.invoke(messages)

        # content = self.llm.invoke(SystemPrompt.collect_missing_params_message(
        #     function_data=function_data, parameter_exists=parameter_exists, prev_question=prev_question), state.user_input, state.thread_id)

        json_data = extract_json(self.clean_llm_output(response.content))
        if not json_data:
            return state

        state.next_step = "select_routine"
        if not json_data.get("isValid", None):
            message = json_data.get("message", "")
            self.context.routine.incomplete.message = message
            self.context.routine.incomplete.missing = json_data.get(
                "missing", [])
            self.context.routine.parameters.update(
                json_data.get("parameters", {}))

            self.context.conversation.extend([
                {"role": "user", "content": state.user_input},
                {"role": "bot", "content": message}
            ])
            state.next_step = "generate_response"

        return state

    def select_routine(self, state: PromptState) -> PromptState:
        prior_context = ""
        parameter_exists = ""
        user_input = state.user_input
        function_data = json.dumps(state.rag_query_results or [])

        if self.context:
            parameter_exists = json.dumps(list(
                self.context.routine.parameters.keys()))
            prior_context = json.dumps(self.context.conversation or [])
            function_data = json.dumps(["%s, %s" % (
                self.context.routine.routine, self.context.routine.description)])

        human_message = HumanMessage(state.user_input)
        system_message = SystemMessage(SystemPrompt.select_routine_message(
                function_data=function_data))
        messages = [system_message] + state.conversation["messages"]

        response = self.llm.invoke(messages)

        # Extract JSON data
        json_data = extract_json(self.clean_llm_output(response.content))
        if not json_data:
            return state

        # Update intent Object
        state.next_step = "call_routine"

        routine = Routine(**json_data)
        routine.incomplete = InCompleteInfo(
            **(json_data.get("incomplete", {}) or {}))

        if not routine.ready:
            # redirect to generate_response to reply to the user
            state.next_step = "generate_response"

            # Store context to collect data
            if not self.context:
                self.context = Context(
                    origin_input=state.user_input, conversation=[])
            if not self.context.routine:
                self.context.routine = routine
            else:
                for key in routine.parameters.keys():
                    if key in self.context.routine.parameters.keys():
                        continue
                    self.context.routine.parameters[key] = routine.parameters[key]
        else:
            state.routine = routine
            self.context = None

        return state

    def call_routine(self, state: PromptState) -> PromptState:
        try:
            routine_path = (state.routine.routine or "").split(".")
            module = importlib.import_module(
                ".".join(routine_path[:-1]))
            func = getattr(module, routine_path[-1])
            state.response_data = func(
                **(state.routine.parameters or {})).response_data
        except:
            state.response_data = ""

        return state

    def generate_response(self, state: PromptState) -> PromptState:
        if self.context:
            state.final_response = self.context.routine.\
                incomplete.message or ""
        else:
            human_message = HumanMessage(state.user_input)
            system_message = SystemMessage(SystemPrompt.response_message(json.dumps(state.response_data)))
            messages = state.conversation["messages"] + \
                [system_message, human_message]

            response = self.llm.invoke(messages)
            state.final_response = self.clean_llm_output(response.content)
            response.content = state.final_response
            state.conversation["messages"].append(response)

        return state

    def handle(self, user_input: str, thread_id: str = ""):
        llm_res = self.graph.invoke({"user_input": user_input}, config={
                                    "configurable": {"thread_id": thread_id}})
        return llm_res.get('final_response', "") or ""
