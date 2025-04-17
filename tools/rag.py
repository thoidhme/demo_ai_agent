from sentence_transformers import SentenceTransformer
from typing import Union, Dict, List, Optional

import os
import json
import yaml
import faiss
import torch
import numpy as np


class DBCollectInfo(object):
    def __init__(self, param_name: str, rag_name: str, rag_system_message: str):
        self.param_name = param_name
        self.rag_name = rag_name
        self.rag_system_message = rag_system_message
        self.rag_query = ""
        self.rag_results = []



class DBCollector(object):
    def __init__(self):
        self.current_index = 0
        self.need_collect = False
        self.data: List[DBCollectInfo] = []

    def add(self, param_name: str, rag_name: str, rag_system_message: str):
        self.need_collect = True
        self.data.append(DBCollectInfo(**{
            "param_name": param_name,
            "rag_name": rag_name,
            "rag_system_message": rag_system_message,
        }))

    def get_collect_info(self) -> DBCollectInfo:
        if self.current_index >= len(self.data):
            return None

        return self.data[self.current_index]

    def set_collect_query(self, query: str):
        if self.current_index >= len(self.data):
            return

        self.data[self.current_index].rag_query = query

    def set_collect_data(self, results: list):
        if self.current_index >= len(self.data):
            return

        self.data[self.current_index].rag_results = results
        if self.current_index == len(self.data):
            self.current_index += 1
        else:
            self.need_collect = False

    def dump_data(self) -> str:
        data = {}
        for item in self.data:
            data[item.param_name] = item.rag_results

        return json.dumps(data) if data else None


class VectorDB(object):
    index_path: str = None
    embedding_path: str = None

    def __init__(self, load=True, model_name: str = 'paraphrase-MiniLM-L6-v2'):
        self.base_data: Optional[Union[Dict[str, int], List[int]]] = None
        self.flat_data: List[str] = self.read_data()

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = SentenceTransformer(model_name, device=device)

        if load or not os.path.exists(self.index_path) or not os.path.exists(self.embedding_path):
            embeddings = self.model.encode(self.flat_data)
            np.save(self.embedding_path, embeddings)

            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)  # dùng L2 distance
            self.index.add(np.array(embeddings))
            faiss.write_index(self.index, self.index_path)
        else:
            self.index = faiss.read_index(self.index_path)
            self.embeddings = np.load(self.embedding_path)

    def read_data(self):
        return []

    def query(self, question: str, k=1) -> List[str]:
        if not question or not self.index or not self.flat_data:
            return []

        # Encode the question
        embedding_question = self.model.encode([question])

        # Defensive check for embedding size mismatch
        if embedding_question.shape[1] != self.index.d:
            raise ValueError("Embedding dimension mismatch with FAISS index.")

        # Perform search
        D, I = self.index.search(np.array(embedding_question), k)

        metric_type = self.index.metric_type
        # Get results with bounds check
        answers = []
        for dist, idx in zip(D[0], I[0]):
            if 0 <= idx < len(self.flat_data):
                # Convert distance to similarity score if needed
                if metric_type == 1:
                    score = 1 / (1 + dist)  # optional: or simply -dist
                elif metric_type == 2:
                    score = dist
                else:
                    score = dist  # fallback

                answers.append(self.flat_data[idx])

        return answers


class RagRoutineYaml(VectorDB):
    index_path: str = './vector_databases/storages/routine.index'
    embedding_path: str = './vector_databases/storages/routine.npy'

    def read_data(self):
        flat_data = []
        with open('./vector_databases/routines.yaml', 'r') as file:
            self.base_data = yaml.safe_load(file)
            for func in self.base_data or []:
                flat_data.append(
                    f"{func.get("routine")}, {func.get("description")}")

        return flat_data


class RagEmployeeJson(VectorDB):
    index_path: str = './vector_databases/storages/employee.index'
    embedding_path: str = './vector_databases/storages/employee.npy'

    def read_data(self):
        flat_data = []
        with open('./vector_databases/employees.json', 'r') as file:
            content = file.read()
            try:
                lines = json.loads(content)
                for human in lines:
                    flat_data.append(f"{human.get("description")}")
            except:
                pass

        return flat_data
