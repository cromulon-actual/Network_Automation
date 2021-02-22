import json
import csv


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
