from flask import Flask, jsonify
from utility import main
from flask_cors import CORS
import json
import os

folder_loc = os.path.dirname(os.path.abspath(__file__))
static_folder = os.path.join(folder_loc, 'build/static')
templates_folder = os.path.join(folder_loc, 'build')

app = Flask(__name__, static_folder=templates_folder, static_url_path='/')
CORS(app)
main()

@app.route('/')
def home():
    return app.send_static_file('index.html')

@app.route(f'/data/<type>')
def get_json(type):
    with open(f'{folder_loc}/json/{type}.json', 'r') as f:
        data = json.load(f)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=False)