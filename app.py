import dash
from flask import Flask, send_from_directory

server = Flask(__name__)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config['suppress_callback_exceptions']=True

app.css.config.serve_locally = True
app.scripts.config.serve_locally = True