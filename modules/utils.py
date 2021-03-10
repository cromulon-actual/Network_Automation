import json
import csv
import yaml
from yaml.loader import FullLoader


def csv_to_dict(filename):  # Create a phone asset dictionary
    f = open(filename)
    csv_dict = dict(csv.reader(f))
    return csv_dict


def wr_to_json(dictionary, filename):
    with open(filename, "w") as f:
        json.dump(dictionary, f, indent=4)


def rd_from_json(filename):
    with open(filename) as f:
        prev_status = json.load(f)
        return prev_status


def pj(dict):
    print(json.dumps(dict, indent=4))


def readYAML(filename):
    with open(filename) as file:
        return yaml.load(file, Loader=FullLoader)


def writeYAML(filename, data):
    with open(filename, 'w') as file:
        yaml.dump(data, file, default_flow_style=False)
