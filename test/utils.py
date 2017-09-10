import json

def from_json_file(filepath):
    with open(filepath, 'r') as fp:
        return json.load(fp)
