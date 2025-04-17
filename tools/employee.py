import json

from common.utils import InfoCollector
from tools.rag import DBCollector
from tools.utils import MissingContextException, RoutineResponse


def create_meeting(raci_guildlines: dict, employees: dict):
    collector = InfoCollector()

    if not raci_guildlines:
        collector.add(param_name="employees", rag_name="employee")
        raise MissingContextException(collector)

    return RoutineResponse("""Data of meeting is: %s""" % json.dumps({
        "raci_guildlines": raci_guildlines,
        "employees": employees,
       
    }), """""")


def find_employees(description: str):
    return description
