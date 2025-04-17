import json
import asyncio
import websockets
import re
import redis

from typing import Dict
from orchestrator import Orchestrator
from llm.engine import GrogEngine
from tools.rag import RagRoutineYaml, RagEmployeeJson, DBCollector, VectorDB

MODEL_NAME = "llama3-70b-8192"
MODEL_NAME = "deepseek-r1-distill-llama-70b"

threads = {}

llm = GrogEngine(MODEL_NAME)
rag_data: Dict[str, VectorDB] = {
    "employee": RagEmployeeJson(True),
    "routine": RagRoutineYaml(True)
}
orchestrator = Orchestrator(llm, rag_data)


async def handle_connection(websocket):
    async for message in websocket:
        message_json = json.loads(message)
        thread_id = message_json.get("id", None)

        result_json = {
            "id": thread_id,
        }

        result_json["result"] = orchestrator.handle(message_json.get("message", ""), thread_id)
        # except Exception as ex:
        #     result_json["result"] = str(ex)

        await websocket.send(json.dumps(result_json))


async def main():
    async with websockets.serve(handle_connection, "localhost", 3001):
        print("WebSocket server running on ws://localhost:3001")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
