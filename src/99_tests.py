# run tests
        
import json
import sys
from os import path

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

with open("test/haiko.json", 'r') as file:
    haiko = json.load(file)

with open("test/test_haiko.json") as file:
    test_json_haiko = json.load(file)

assert(haiko == test_json_haiko)