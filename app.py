import hashlib
import json
from time import time
from flask import Flask, request, render_template, redirect, url_for
from flask_socketio import SocketIO, emit

class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        """Calculates SHA-256 hash of the block."""
        block_string = json.dumps(self.__dict__, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        """Creates the initial block (genesis block)."""
        timestamp = time()
        data = "Genesis Block"
        previous_hash = "0"
        self.chain.append(Block(0, timestamp, data, previous_hash))

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, block):
        """Adds a new block to the chain after verifying its hash."""
        previous_block = self.get_latest_block()
        if block.previous_hash != previous_block.hash:
            return False
        self.chain.append(block)
        return True

    def proof_of_work(self, block):
        """Simple Proof of Work (PoW) implementation."""
        while True:
            block.hash = block.calculate_hash()
            if block.hash[:4] == '0000':  # Adjust difficulty as needed
                break
            block.data += '0'

    def chain_valid(self):
        """Validates the integrity of the blockchain."""
        current_index = 1
        for block in self.chain[1:]:
            previous_block = self.chain[current_index - 1]
            if block.hash != block.calculate_hash():
                return False
            if block.previous_hash != previous_block.hash:
                return False
            current_index += 1
        return True

blockchain = Blockchain()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a strong secret key
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html', chain=blockchain.chain)


from flask import redirect, url_for

@app.route('/add_data', methods=['POST'])
def add_data():
    data = request.form['data']  # Access form data using request.form
    previous_block = blockchain.get_latest_block()
    previous_hash = previous_block.hash
    new_block = Block(len(blockchain.chain), time(), data, previous_hash)
    blockchain.proof_of_work(new_block)

    if blockchain.add_block(new_block):
        socketio.emit('new_block', json.dumps(new_block.__dict__))
        return redirect(url_for('index'))  # Redirect to the index route
    else:
        return 'Failed to add block!', 400


@socketio.on('connect')
def handle_connect():
    socketio.emit('chain_updated', json.dumps(blockchain.chain))

if __name__ == '__main__':
    socketio.run(app, debug=True)
