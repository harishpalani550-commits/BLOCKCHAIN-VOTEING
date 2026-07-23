"""
blockchain_voting_single_file.py

A complete Blockchain-based Secure Voting System in ONE file.
Includes: blockchain core, voting logic, and Flask web app with inline HTML.

HOW TO RUN:
    1. pip install flask
    2. python3 blockchain_voting_single_file.py
    3. Open http://127.0.0.1:5000 in your browser
"""

import hashlib
import json
import time
import uuid

from flask import Flask, request, redirect, url_for, flash, jsonify, render_template_string


# ======================================================
# 1. BLOCKCHAIN CORE
# ======================================================
class Block:
    def __init__(self, index, timestamp, votes, previous_hash, nonce=0):
        self.index = index
        self.timestamp = timestamp
        self.votes = votes
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "votes": self.votes,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "votes": self.votes,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash
        }


class Blockchain:
    DIFFICULTY = 3

    def __init__(self):
        self.chain = []
        self.pending_votes = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis = Block(0, time.time(), [], "0")
        genesis.hash = self.proof_of_work(genesis)
        self.chain.append(genesis)

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, block):
        block.nonce = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith("0" * self.DIFFICULTY):
            block.nonce += 1
            computed_hash = block.compute_hash()
        return computed_hash

    def add_vote(self, vote):
        self.pending_votes.append(vote)

    def mine_pending_votes(self):
        if not self.pending_votes:
            return None
        new_block = Block(
            index=self.last_block.index + 1,
            timestamp=time.time(),
            votes=self.pending_votes,
            previous_hash=self.last_block.hash
        )
        new_block.hash = self.proof_of_work(new_block)
        self.chain.append(new_block)
        self.pending_votes = []
        return new_block

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            if current.hash != current.compute_hash():
                return False, f"Block {current.index} data has been tampered with."
            if current.previous_hash != previous.hash:
                return False, f"Block {current.index} is not linked correctly to previous block."
            if not current.hash.startswith("0" * self.DIFFICULTY):
                return False, f"Block {current.index} does not satisfy proof-of-work."
        return True, "Blockchain is valid."

    def get_all_votes(self):
        votes = []
        for block in self.chain:
            votes.extend(block.votes)
        return votes

    def to_list(self):
        return [block.to_dict() for block in self.chain]


# ======================================================
# 2. VOTING SYSTEM LOGIC
# ======================================================
class VotingSystem:
    def __init__(self, blockchain):
        self.blockchain = blockchain
        self.registered_voters = {}
        self.candidates = set()

    def add_candidate(self, name):
        self.candidates.add(name)

    def register_voter(self, name, national_id):
        voter_id = str(uuid.uuid4())
        id_hash = hashlib.sha256(national_id.encode()).hexdigest()
        for v in self.registered_voters.values():
            if v["id_hash"] == id_hash:
                return None, "This national ID is already registered."
        self.registered_voters[voter_id] = {
            "name": name,
            "id_hash": id_hash,
            "has_voted": False
        }
        return voter_id, "Registration successful."

    def cast_vote(self, voter_id, candidate):
        if voter_id not in self.registered_voters:
            return False, "Voter not registered."
        voter = self.registered_voters[voter_id]
        if voter["has_voted"]:
            return False, "This voter has already cast a vote."
        if candidate not in self.candidates:
            return False, "Invalid candidate."
        vote = {
            "voter_hash": hashlib.sha256(voter_id.encode()).hexdigest(),
            "candidate": candidate,
            "timestamp": time.time()
        }
        self.blockchain.add_vote(vote)
        self.blockchain.mine_pending_votes()
        voter["has_voted"] = True
        return True, "Vote cast and recorded on the blockchain."

    def tally_votes(self):
        results = {c: 0 for c in self.candidates}
        for vote in self.blockchain.get_all_votes():
            if vote["candidate"] in results:
                results[vote["candidate"]] += 1
        return results


# ======================================================
# 3. FLASK WEB APP (HTML embedded as strings)
# ======================================================
app = Flask(__name__)
app.secret_key = "change-this-secret-key"

blockchain = Blockchain()
voting_system = VotingSystem(blockchain)

for candidate in ["Candidate A", "Candidate B", "Candidate C"]:
    voting_system.add_candidate(candidate)


HOME_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Blockchain Voting System</title>
<style>
body { font-family: Arial, sans-serif; max-width: 700px; margin: 40px auto; padding: 0 20px; background:#f5f6fa; }
h1 { color: #2c3e50; }
.card { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }
input, select { width: 100%; padding: 8px; margin: 6px 0 14px; border: 1px solid #ccc; border-radius: 6px; }
button { background: #2c3e50; color: white; border: none; padding: 10px 16px; border-radius: 6px; cursor: pointer; }
button:hover { background: #1a252f; }
.flash { padding: 10px; border-radius: 6px; margin-bottom: 14px; }
.success { background: #d4edda; color: #155724; }
.error { background: #f8d7da; color: #721c24; }
a { color: #2c3e50; }
</style>
</head>
<body>
<h1>🗳 Blockchain Voting System</h1>

{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    {% for category, message in messages %}
      <div class="flash {{ category }}">{{ message }}</div>
    {% endfor %}
  {% endif %}
{% endwith %}

<div class="card">
    <h2>1. Register to Vote</h2>
    <form action="/register" method="POST">
        <label>Full Name</label>
        <input type="text" name="name" required>
        <label>National ID</label>
        <input type="text" name="national_id" required>
        <button type="submit">Register</button>
    </form>
</div>

<div class="card">
    <h2>2. Cast Your Vote</h2>
    <form action="/vote" method="POST">
        <label>Voter ID</label>
        <input type="text" name="voter_id" required>
        <label>Candidate</label>
        <select name="candidate" required>
            {% for c in candidates %}
            <option value="{{ c }}">{{ c }}</option>
            {% endfor %}
        </select>
        <button type="submit">Vote</button>
    </form>
</div>

<div class="card">
    <p><a href="/results">View Results</a> | <a href="/api/chain">View Raw Blockchain (JSON)</a> | <a href="/api/verify">Verify Chain Integrity</a></p>
</div>
</body>
</html>
"""

RESULTS_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Election Results</title>
<style>
body { font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; background:#f5f6fa; }
h1 { color: #2c3e50; }
table { width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; }
th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
th { background: #2c3e50; color: white; }
a { display:inline-block; margin-top: 20px; color: #2c3e50; }
</style>
</head>
<body>
<h1>📊 Live Results</h1>
<table>
    <tr><th>Candidate</th><th>Votes</th></tr>
    {% for candidate, count in results.items() %}
    <tr><td>{{ candidate }}</td><td>{{ count }}</td></tr>
    {% endfor %}
</table>
<a href="/">&larr; Back to voting</a>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HOME_PAGE, candidates=voting_system.candidates)


@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name", "").strip()
    national_id = request.form.get("national_id", "").strip()

    if not name or not national_id:
        flash("Name and National ID are required.", "error")
        return redirect(url_for("home"))

    voter_id, message = voting_system.register_voter(name, national_id)
    if voter_id:
        flash(f"Registered! Your Voter ID (save this): {voter_id}", "success")
    else:
        flash(message, "error")
    return redirect(url_for("home"))


@app.route("/vote", methods=["POST"])
def vote():
    voter_id = request.form.get("voter_id", "").strip()
    candidate = request.form.get("candidate", "").strip()

    success, message = voting_system.cast_vote(voter_id, candidate)
    flash(message, "success" if success else "error")
    return redirect(url_for("home"))


@app.route("/results")
def results():
    return render_template_string(RESULTS_PAGE, results=voting_system.tally_votes())


@app.route("/api/chain")
def api_chain():
    return jsonify(blockchain.to_list())


@app.route("/api/verify")
def api_verify():
    valid, message = blockchain.is_chain_valid()
    return jsonify({"valid": valid, "message": message})


if __name__ == "__main__":
    app.run(debug=True)
