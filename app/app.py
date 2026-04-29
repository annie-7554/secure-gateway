from flask import Flask, request, jsonify
app = Flask(__name__)

# Simple in-memory store (for demo only)
notes = []

@app.route('/health')
def health():
    return jsonify({'status':'ok'})

@app.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    if username == 'admin' and password == 'password':
        return jsonify({'token':'demo-token'})
    return jsonify({'error':'invalid credentials'}), 401

@app.route('/notes', methods=['GET','POST'])
def notes_route():
    if request.method == 'POST':
        data = request.json or {}
        note = data.get('note')
        notes.append(note)
        return jsonify({'note':note}), 201
    return jsonify({'notes':notes})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
