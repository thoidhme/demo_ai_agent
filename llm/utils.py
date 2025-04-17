import re
import json
from typing import List


def extract_json(json_str: str, model: str = '') -> List[any]:
    json_data = []
    pattern = r"```json\s*(.*?)\s*```"
    matches = re.findall(pattern, json_str, re.DOTALL)

    if not matches:
        return []

    for match in matches:
        try:
            json_data.append(json.loads(match.replace("\n", "").strip()))
        except Exception as ex:
            print(ex)
            pass

    return json_data
