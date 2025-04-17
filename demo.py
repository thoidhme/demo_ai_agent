import uuid
import time

from llm.engine import GrogEngine
from langgraph.graph import START, MessagesState, StateGraph

# MODEL_NAME = "allam-2-7b"
MODEL_NAME = "deepseek-r1-distill-llama-70b"
MODEL_NAME = "llama3-70b-8192"

threads = {}

model = GrogEngine(MODEL_NAME) 
response = model.invoke([
    {   
        "role": "system",
        "content": """"Bạn là một trợ lý AI. Nhiệm vụ của bạn là phân tích câu hỏi của người dùng và xác định:
- Ý định của người dùng.
- Trích xuất thông tin đầu vào nếu có."
""",
    },
    {"role": "user", "content": "Thời tiết hôm nay thế nào"},
])
# Define a new graph
workflow = StateGraph(state_schema=MessagesState)

# Define the function that calls the model
def call_model(state: MessagesState):

# A: Bắt đầu
    start = time.time()
    response = model.invoke(state["messages"])
    end = time.time()
    print(f"{MODEL_NAME} Thời gian xử lý: {end - start:.4f} giây")
    return {"messages": response}


# Define the two nodes we will cycle between
workflow.add_edge(START, "model")
workflow.add_node("model", call_model)

# Add memory
# memory = MemorySaver()
app = workflow.compile()


# The thread id is a unique key that identifies
# this particular conversation.
# We'll just generate a random uuid here.
thread_id = uuid.uuid4()
config = {"configurable": {"thread_id": thread_id}}

app.invoke
input_messages = [
    {   
        "role": "system",
        "content": """"Bạn là một trợ lý AI. Nhiệm vụ của bạn là phân tích câu hỏi của người dùng và xác định:
- Ý định của người dùng.
- Trích xuất thông tin đầu vào nếu có."
""",
    },
    {"role": "user", "content": "Thời tiết hôm nay thế nào"},
]

ress =  app.invoke({"messages": input_messages}, config)
print(ress)

# input_messages = [
#     {"role": "user", "content": "Giá từ 18tr"}]
# for event in app.stream({"messages": input_messages}, config, stream_mode="values"):
#     event["messages"][-1].pretty_print()

# input_messages = [
#     {"role": "user", "content": "đến 20tr"}]
# for event in app.stream({"messages": input_messages}, config, stream_mode="values"):
#     event["messages"][-1].pretty_print()

# input_messages = [
#     {"role": "user", "content": "màu vàng"}]
# for event in app.stream({"messages": input_messages}, config, stream_mode="values"):
#     event["messages"][-1].pretty_print()

# input_messages = [
#     {"role": "user", "content": "Apple"}]
# for event in app.stream({"messages": input_messages}, config, stream_mode="values"):
#     event["messages"][-1].pretty_print()