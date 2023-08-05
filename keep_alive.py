from flask import Flask, send_file
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return send_file('templates/index.html')

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == '__main__':
    keep_alive()
