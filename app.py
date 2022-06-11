import os

from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from secret import secretpassword

app = Flask(__name__)
app.secret_key = secretpassword
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

@app.route("/helperform",methods=["GET","POST"])
def helperform():

    if request.method == "POST":
        
        if request.form.get("passwordone") != request.form.get("passwordtwo"):
            flash("Password do not match")
            return redirect("/helperform")
        
        else:
            password = request.form.get("passwordtwo")
            if len(password) < 8:
                flash("Password must be at least 8 characters long")
                return redirect("/helperform")
            
            else:
                password = generate_password_hash
                email = request.form.get("email")
                if "@u.nus.edu" not in email:
                    flash("Invalid email address")
                    return redirect("/helperform")
                
                else:
                    -
                    # TODO: checks database of helpers if name is already taken (If/Else check)
                    name = request.form.get("name")
                    telegram = request.form.get("telegram")
                    if request.form.get("github"):
                        github = request.form.get("github")
                    else:
                        github = ""
                    time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    return render_template("helperform.html", time=time)              
    
    else:
        time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        return render_template("helperform.html", time=time)  
    
if __name__ == '__main__':
    app.debug = True
    app.run()