from flask import Flask, jsonify
import random

app = Flask(__name__)

@app.get("/demo")
def random_number():
    return jsonify({
        "value": random.randint(1, 100),
        "status": "ok"
    })

if __name__ == "__main__":
    app.run(port=5001, debug=True)
