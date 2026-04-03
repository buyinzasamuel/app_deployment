from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'My cloud deployment is successful!'

if __name__ == '__main__':
    app.run(debug=True)

    