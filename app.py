import os

from cs50 import SQL
from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required, admin_only
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


@app.route("/helpers",methods=["GET","POST"])
def helpers():
    
    if request.method == "POST" and request.form["btn"] == "login":
        email = request.form.get("email")
        password = request.form.get("password")
        rows = db.execute("SELECT * FROM helpers WHERE email = ?", email)
        
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            flash("Invalid Login","error")
            return redirect("/helpers")

        else:
            session["user_id"] = rows[0]["id"]
            flash("Login successful","info")
            return redirect("/helpers")
        
    elif request.method == "POST" and request.form["btn"] == "change":
        email = request.form.get("email")
        oldpassword = request.form.get("oldpassword")
        rows = db.execute("SELECT * FROM helpers WHERE email = ?", email)
        passwordone = request.form.get("passwordone")
        passwordtwo = request.form.get("passwordtwo")
        
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], oldpassword):
            flash("Invalid Email or Password.","error")
            return redirect("/helpers")
        
        elif passwordone != passwordtwo:
            flash("Passwords do not match.","error")
            return redirect("/helpers")
        
        elif oldpassword == passwordtwo:
            flash("Wait, I thought you were changing your password? Please key in ANOTHER password.","error")
            return redirect("/helpers")
        
        elif len(passwordtwo) < 8:
            flash("Password must be at least 8 characters.","error")
            return redirect("/helpers")
        
        else:
            hash = generate_password_hash(passwordtwo)
            db.execute("UPDATE helpers SET hash = ? WHERE email = ?", hash, email)
            session.clear()
            flash("Password successfully updated. Please relogin.","info")
            return redirect("/helpers")
        
    else:
        time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        return render_template("helpers.html", time=time)


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    flash("Logout successful","info")
    return redirect("/helpers")


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
@admin_only
def adminpage():
    
    helperformDB = db.execute("SELECT * FROM Helpersform")
    helperDB = db.execute("SELECT * FROM Helpers")
    nonmodulesDB = db.execute("SELECT * FROM Modules WHERE approved = 2")
    mModuleDB = db.execute("SELECT * FROM Modules WHERE code LIKE '%/%' ")
    
    if request.method == "POST" and request.form["adminbtn"] == "approvehelper":
        
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
    
    elif request.method == "POST" and request.form.get("adminbtn") == "ban":
        email = request.form.get("email")
        db.execute("DELETE from Helpers WHERE email = ?", email)
        return redirect("/adminpage")
    
    elif request.method == "POST" and request.form.get("adminbtn") == "approvetwo":
        db.execute("UPDATE Modules SET approved = 1 WHERE modlink = ?", request.form.get("link"))
        return redirect("/adminpage")
    
    elif request.method == "POST" and request.form.get("adminbtn") == "reject":
        db.execute("DELETE from Modules WHERE modlink = ?", request.form.get("link"))
        return redirect("/adminpage")
    
    elif request.method == "POST" and request.form.get("adminbtn") == "edit":
        row = db.execute("SELECT * FROM Modules WHERE modlink = ?", request.form.get("link"))
        time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        redirect("/editmodule")
        return render_template("editmodule.html", module=row[0], time=time)
    
    elif request.method == "POST" and request.form.get("adminbtn") == "split":
        row = db.execute("SELECT * FROM Modules WHERE modlink = ?", request.form.get("link"))
        codes = row[0]["code"].split("/")
        db.execute("UPDATE Modules SET code = ?, approved = ? WHERE modlink = ?", codes[0], 2, row[0]["modlink"])
        for code in range(1, len(codes)):
            db.execute("INSERT INTO Modules (code, name, mc, modlink, semone, semtwo, semthree, semfour, approved) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", codes[code], row[0]["name"], row[0]["mc"], row[0]["modlink"], row[0]["semone"], row[0]["semtwo"], row[0]["semthree"], row[0]["semfour"], 2)
        return redirect("/adminpage")
    
    else:
        time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        return render_template("admin.html", time=time, helpersform=helperformDB, helpers=helperDB, nonmodules=nonmodulesDB, Mmodules=mModuleDB)


@app.route("/moduleform",methods=["GET","POST"])
def moduleform():
    
    moduleDB = db.execute("SELECT * FROM Modules")
    
    if request.method == "POST" and request.form.get("offerone") == None and request.form.get("offertwo") == None and request.form.get("offertree") == None and request.form.get("offerfour") == None: 
        flash("Please indicate which semester/s the module is offered","error")
        return redirect("/moduleform")
    
    elif request.method == "POST" and request.form.get("btn") == "submit":
        
        code = request.form.get("modulecode")
        name = request.form.get("modulename")
        mc = request.form.get("modulecredits")
        link = request.form.get("modulelink")
        m = db.execute("SELECT * FROM Modules WHERE code = ?", code)
        
        if len(m) == 1:
            flash("Module in the system!","error")
            return redirect("/moduleform")
        
        else:
            semone = 1 if request.form.get("offerone") == "semone" else 0
            semtwo = 1 if request.form.get("offertwo") == "semtwo" else 0
            semthree = 1 if request.form.get("offerthree") == "semthree" else 0
            semfour = 1 if request.form.get("offerfour") == "semfour" else 0
            db.execute("INSERT INTO Modules (code, name, mc, modlink, semone, semtwo, semthree, semfour) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", code, name, mc, link, semone, semtwo, semthree, semfour)
            flash("Module successfully submitted! Please wait for the staff to approve.","info")
            return redirect("/moduleform")
        
    elif request.method == "POST" and request.form.get("btn") == "resubmit":
        
        code = request.form.get("modulecode")
        mc = request.form.get("modulecredits")
        link = request.form.get("modulelink")
        m = db.execute("SELECT * FROM Modules WHERE code = ?", code)
        
        if len(m) != 1:
            flash("Module not in the system!","error")
            return redirect("/moduleform")
        
        else:
            semone = 1 if request.form.get("offerone") == "semone" else 0
            semtwo = 1 if request.form.get("offertwo") == "semtwo" else 0
            semthree = 1 if request.form.get("offerthree") == "semthree" else 0
            semfour = 1 if request.form.get("offerfour") == "semfour" else 0
            db.execute("UPDATE Modules SET mc = ?, modlink = ?, semone = ?, semtwo = ?, semthree = ?, semfour = ?, approved = ? WHERE code = ?", mc, link, semone, semtwo, semthree, semfour, 0, code)
            flash("Module successfully submitted! Please wait for the staff to approve.","info")
            return redirect("/moduleform")
        
    else:
        time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        return render_template("moduleform.html", time=time)


@app.route("/contribute",methods=["GET","POST"])
@login_required
def contribute():
    
    helperDB = db.execute("SELECT * FROM Helpers WHERE id = ?", session.get("user_id")) 
    moduleDB = db.execute("SELECT * FROM Modules WHERE approved = 0 AND code NOT LIKE '%/%'")
    
    if request.method == "POST" and request.form.get("btn") == "approve":
        db.execute("UPDATE Modules SET approved = 1 WHERE modlink = ?", request.form.get("link"))
        return redirect("/contribute")
    
    elif request.method == "POST" and request.form.get("btn") == "unsure":
        db.execute("UPDATE Modules SET approved = 2 WHERE modlink = ?", request.form.get("link"))
        return redirect("/contribute")
    
    else:
        time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        return render_template("contribute.html", time=time, modules=moduleDB, email=helperDB[0]["email"])
    

@app.route("/editmodule",methods=["GET","POST"])
@admin_only
def editmodule():
    
    if request.method == "POST":
        
        if request.form.get("modulecode"):
            db.execute("UPDATE Modules SET code = ? WHERE modlink = ?", request.form.get("modulecode"), request.form.get("link"))
        
        if request.form.get("modulename"):
            db.execute("UPDATE Modules SET name = ? WHERE modlink = ?", request.form.get("modulename"), request.form.get("link"))
        
        if request.form.get("modulecredits"):
            db.execute("UPDATE Modules SET mc = ? WHERE modlink = ?", request.form.get("modulecredits"), request.form.get("link"))
        
        if request.form.get("modulelink"):
            moduleOfInterest = db.execute("SELECT * FROM Modules WHERE modlink = ?", request.form.get("link"))
            db.execute("UPDATE Modules SET modlink = ? WHERE code = ?", request.form.get("modulelink"), moduleOfInterest[0]["code"])
            
        semone = 1 if request.form.get("offerone") == "semone" else 0
        semtwo = 1 if request.form.get("offertwo") == "semtwo" else 0
        semthree = 1 if request.form.get("offerthree") == "semthree" else 0
        semfour = 1 if request.form.get("offerfour") == "semfour" else 0
        moduleOfInterest = db.execute("SELECT * FROM Modules WHERE modlink = ?", request.form.get("link"))
        db.execute("UPDATE Modules SET semone = ?, semtwo = ?, semthree = ?, semfour = ?, approved = ? WHERE code = ?", semone, semtwo, semthree, semfour, 0, moduleOfInterest[0]["code"])
        flash("Module successfully edited!","info")
        return redirect("/adminpage")
        
    else:
        row = db.execute("SELECT * FROM Modules WHERE modlink = ?", request.form.get("link"))
        time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        return render_template("editmodule.html", module=row[0], time=time)
    
if __name__ == '__main__':
    app.debug = True
    app.run()