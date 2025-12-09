import os
import json


def read_data(dir, json_file):
    data_path = os.path.join("tests", "checks", dir, json_file)
    with open(data_path, "r") as file:
        data = json.load(file)
    return data
