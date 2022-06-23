from flask import Flask
from flask_cors import CORS
import socket

print(socket.gethostbyname(socket.gethostname()))

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return '<div>11</div>'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)