import os

from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():
    time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return render_template("index.html", time=time)

@app.route("/helpers",methods=["GET"])
def helpers():
    time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return render_template("helpers.html", time=time)

@app.route("/helperform",methods=["GET"])
def helperform():
    time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return render_template("helperform.html", time=time)