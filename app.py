import os

from cs50 import SQL
from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from secret import secretpassword

app = Flask(__name__)
app.secret_key = secretpassword
app.config["TEMPLATES_AUTO_RELOAD"] = True
db = SQL("sqlite:///planner.db")

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
        
        password = request.form.get("passwordtwo")
        email = request.form.get("email")
        telegram = request.form.get("telegram")
        
        if request.form.get("github"):
            github = request.form.get("github")
            
        else:
            github = ""
     
        if request.form.get("passwordone") != password:
            flash("Password do not match","error")
            return redirect("/helperform")
        
        elif len(password) < 8:
                flash("Password must be at least 8 characters long","error")
                return redirect("/helperform")
            
        else:
            hashed = generate_password_hash(password)
                
            if "@u.nus.edu" not in email:
                flash("Invalid email address","error")
                return redirect("/helperform")
                
            else:
                
                helperformDB = db.execute("SELECT * FROM Helpersform WHERE email = ?", email)
                helperDB = db.execute("SELECT * FROM Helpers WHERE email = ?", email) 
                
                if len(helperformDB) == 1 or len(helperDB) == 1:
                    flash("You already have an account registered!","error")
                    return redirect("/helperform")
                
                else:
                    db.execute("INSERT INTO Helpersform (email, telegram, github, hash) VALUES (?, ?, ?, ?)", email, telegram, github, hashed)
                    flash("You have successfully registered! Please wait to be contacted!","success")
                    return redirect("/helpers")
            
    else:
        time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        return render_template("helperform.html", time=time)  

@app.route("/adminpage",methods=["GET","POST"])
def adminpage():
    
    helperformDB = db.execute("SELECT * FROM Helpersform")
    helperDB = db.execute("SELECT * FROM Helpers")
    
    if request.method == "POST" and request.form["adminbtn"] == "approve":
        
        if request.form.get("messaged") == None or request.form.get("recieved") == None or not (request.form.get("major")):
            flash("Please go and verify the user first, YS!","error")
            return redirect("/adminpage")
        
        else:
            email = request.form.get("email")
            telegram = request.form.get("telegram")
            
            if request.form.get("github"):
                github = request.form.get("github")
            
            else:
                github = ""
            
            password = helperformDB[0]["hash"]
            major = request.form.get("major")
            db.execute("DELETE from HelpersForm WHERE email = ?", email)
            db.execute("INSERT INTO Helpers(email, telegram, github, hash, major) VALUES (?, ?, ?, ?, ?)", email, telegram, github, password, major)
            return redirect("/adminpage")   
    
    elif request.method == "POST" and request.form["adminbtn"] == "ban":
        email = request.form.get("email")
        db.execute("DELETE from Helpers WHERE email = ?", email)
        return redirect("/adminpage") 

    else:
        time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        return render_template("admin.html", time=time, helpersform=helperformDB, helpers=helperDB)

if __name__ == '__main__':
    app.debug = True
    app.run()