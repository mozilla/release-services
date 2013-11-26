from flask import Flask
app = Flask('releng-api')

@app.route('/')
def hello():
    return "Hello"

app.run(host='0.0.0.0', debug=True)
