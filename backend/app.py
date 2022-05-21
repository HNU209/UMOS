from flask import Flask, jsonify
from utility import get_data
from flask_cors import CORS
import json
import os

folder_loc = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
CORS(app)

@app.route(f'/data/<type>')
def get_json(type):
    get_data(type)
    with open(f'{folder_loc}/json/{type}.json', 'r') as f:
        data = json.load(f)
    return jsonify(data)

if __name__ == '__main__':
    app.run()