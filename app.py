import os
from re import I
import re
from tkinter.messagebox import YESNOCANCEL

from pkg_resources import require

from cs50 import SQL
from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session, make_response, jsonify
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required, admin_only, load_plan_as_session
from secret import secretpassword

app = Flask(__name__)
app.secret_key = secretpassword
app.config["TEMPLATES_AUTO_RELOAD"] = True
SESSION_COOKIE_SECURE = True
REMEMBER_COOKIE_SECURE = True
db = SQL("sqlite:///planner.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/",methods=["GET","POST"])
def index():
    
    alphaBets = ("Y", "X", "W", "U", "R", "N", "M", "L", "J", "H", "E", "A", "B")
    degrees = db.execute("SELECT * FROM degrees")
    time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    # when user wants to load existing plan
    if request.method == "POST" and request.form["btn"] == "load":
        planname = request.form.get("planname")
        planDB = db.execute("SELECT * FROM Plans")
        
        # checks validity of their matriculation / nusnet id
        if len(planname) != 8 or not (planname[:3].isdigit and planname[3] in alphaBets and planname[4:].isdigit): 
            flash("Invalid matriculation number or NUSNET ID.", "error")
            return redirect("/")
        
        # check if user has already has a plan
        if len(planDB)!= 0:
            for i in range(len(planDB)):
                if (check_password_hash(planDB[i]["hashname"], planname)):
                    planDB = db.execute("SELECT * FROM Plans WHERE id = ?", (i + 1))
                    flash("Plan successfully loaded!", "success")
                    session["user_id"] = int(planDB[0]["id"]) + 500
                    return redirect("/plan")
                    break
        
        # rejects when planname not found
        else:
            flash("Please create a plan first!", "error")
            return redirect("/")
                
    # when user selects year and degree
    elif request.method == "POST" and (request.form["btn"] == "create"):
        planname = request.form.get("planname")
        planDB = db.execute("SELECT * FROM Plans")
        
        if not planname:
            flash("Please enter your matriculatio number and NUSNET ID!", "error")
            return redirect("/")
        
        # check if user has already has a plan (if does prompt error, else creates)
        if len(planDB)!= 0:
            for i in range(len(planDB)):
                if (check_password_hash(planDB[i]["hashname"], planname)):
                    flash("Plan already exist! Just load the existing plan or save / update the plan.", "error")   
                    return redirect("/")
                    break
                
            else:
                year = request.form.get("year")
                degreename = request.form.get("degree")
                
                if not year or not request.form.get("degree"):
                    flash("Please fill up year / degree.", "error")
                    return redirect("/")
                
                spec = 1 if request.form.get("spec") == "spec" else 0
                secondmajor = 1 if request.form.get("secondmajor") == "secondmajor" else 0
                minorone = 1 if request.form.get("minorone") == "minorone" else 0
                minortwo = 1 if request.form.get("minortwo") == "minortwo" else 0
                minorthree = 1 if request.form.get("minorthree") == "minorthree" else 0
                
                if not ((minorone == 0 and minortwo == 0 and minorthree == 0) or (minorone == 1 and minortwo == 0 and minorthree == 0) or (minorone == 1 and minortwo == 1 and minorthree == 0) or (minorone == 1 and minortwo == 1 and minorthree == 1)):
                    flash("Please select 1st Minor first, followed by 2nd Minor then 3rd Minor.", "error")
                    return redirect("/")
                
                degreeID = db.execute("SELECT id FROM Degrees WHERE degreename = ?", degreename)
                db.execute("INSERT INTO Plans (hashname, year, degreename, spec, secondmajor, minorone, minorone, minorthree) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", generate_password_hash(planname), year, degreeID[0]["id"], spec, secondmajor, minorone, minortwo, minorthree)
                planDB = db.execute("SELECT * FROM Plans WHERE id = ?", len(planDB))
                flash("Plan successfully created!", "success")
                session["user_id"] = int(planDB[0]["id"]) + 500
                return redirect("/plan")
    
    # check if user has already has a plan (if does updates)  
    elif request.method == "POST" and (request.form["btn"] == "update"):
        planname = request.form.get("planname")
        planDB = db.execute("SELECT * FROM Plans")
        
        if not planname:
            flash("Please enter your matriculatio number and NUSNET ID!", "error")
            return redirect("/")
            
        if len(planDB)!= 0:
            for i in range(len(planDB)):
                if (check_password_hash(planDB[i]["hashname"], planname)):
                    year = request.form.get("year")
                    degreename = request.form.get("degree")
                    
                    if not year or not degreename:
                        flash("Please fill up year / degree.", "error")
                        return redirect("/")
                    
                    spec = 1 if request.form.get("spec") == "spec" else 0
                    secondmajor = 1 if request.form.get("secondmajor") == "secondmajor" else 0
                    minorone = 1 if request.form.get("minorone") == "minorone" else 0
                    minortwo = 1 if request.form.get("minortwo") == "minortwo" else 0
                    minorthree = 1 if request.form.get("minorthree") == "minorthree" else 0
                    
                    if not ((minorone == 0 and minortwo == 0 and minorthree == 0) or (minorone == 1 and minortwo == 0 and minorthree == 0) or (minorone == 1 and minortwo == 1 and minorthree == 0) or (minorone == 1 and minortwo == 1 and minorthree == 1)):
                        flash("Please select 1st Minor first, followed by 2nd Minor then 3rd Minor.", "error")
                        return redirect("/")
                    
                    degreeID = db.execute("SELECT id FROM Degrees WHERE degreename = ?", degreename)
                    db.execute("UPDATE Plans SET year = ?, degreename = ?, spec = ?, secondmajor = ?, minorone = ?, minortwo = ?, minorthree = ? WHERE id = ?", year, degreeID[0]["id"], spec, secondmajor, minorone, minortwo, minorthree, (i+1))
                    planDB = db.execute("SELECT * FROM Plans WHERE id = ?", len(planDB))
                    flash("Plan successfully updated!", "success")
                    session["user_id"] = int(planDB[0]["id"]) + 500
                    return redirect("/plan")
                    break
                
            else:
                flash("Plan not found! Please create a plan first.", "error")
                return redirect("/")
                         
    else:
        return render_template("index.html", time=time, degrees=degrees)


@app.route("/plan",methods=["GET","POST"])
@load_plan_as_session
def plan():
    
    time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    planID = session["user_id"] - 500
    plan = db.execute("SELECT * FROM Plans WHERE id = ?", planID)
    requirements = db.execute("SELECT * FROM Requirements WHERE degreeid = ?", plan[0]["degreename"])
    
    # adds modules to Y1S1
    if request.method == "POST" and (request.form["btn"] == "addoneone"):
        
        oneonemod = request.form.get("oneonemod")
        if not oneonemod or not request.form.get("oneoneueqns") or not request.form.get("oneonegrade"):
            flash("Please fill up the module code, U.E and grade in that row!", "error")
            return redirect("/plan")
        
        # checks for duplicate values
        
        typeone = request.form.get("oneonetypeone")
        typetwo = request.form.get("oneonetypetwo")
        typethree = request.form.get("oneonetypethree")
        
        # all majors
        if (typeone == "major" and typetwo == "major"):
            flash("Please dont select the same types!", "error")
            return redirect("/plan")
        
        # all second majors
        if (typeone == "majortwo" and typetwo == "majortwo") or (typeone == "majortwo" and typethree == "majortwo") or (typetwo == "majortwo" and typethree == "majortwo") or (typeone == "majortwo" and typetwo == "majortwo" and typethree == "majortwo"):
            flash("Please dont select the same types!", "error")
            return redirect("/plan")
        
        # all minorone
        if (typeone == "minorone" and typetwo == "minorone") or (typeone == "minorone" and typethree == "minorone") or (typetwo == "minorone" and typethree == "minorone") or (typeone == "minorone" and typetwo == "minorone" and typethree == "minorone"):
            flash("Please dont select the same types!", "error")
            return redirect("/plan")
        
        # all minortwo
        if (typeone == "minortwo" and typetwo == "minortwo") or (typeone == "minortwo" and typethree == "minortwo") or (typetwo == "minortwo" and typethree == "minortwo") or (typeone == "minortwo" and typetwo == "minortwo" and typethree == "minortwo"):
            flash("Please dont select the same types!", "error")
            return redirect("/plan")
        
        # all minorthree
        if (typeone == "minorthree" and typetwo == "minorthree") or (typeone == "minorthree" and typethree == "minorthree") or (typetwo == "minorthree" and typethree == "minorthree") or (typeone == "minorthree" and typetwo == "minorthree" and typethree == "minorthree"):
            flash("Please dont select the same types!", "error")
            return redirect("/plan")
        
        ModOneOne = db.execute("SELECT * FROM Modules WHERE code = ? AND semone = ? AND approved = ?", oneonemod, 1, 1)
        if len(ModOneOne) != 1:
            flash("Invalid Module Code or Module Not Avaliable in Semester 1!", "error")
            return redirect("/plan")
        
        elif ModOneOne:
            
            DuplicateOneOne = db.execute("SELECT * FROM yearonesemone WHERE modulecode = ?", ModOneOne[0]["code"])
            
            if len(DuplicateOneOne) == 1:
                flash("Module already in plan!", "error")
                return redirect("/plan")
        
        db.execute("INSERT INTO yearonesemone (planid, modulecode, typeone, typetwo, typethree, ue, grade) VALUES (?, ?, ?, ?, ?, ?, ?)", planID, ModOneOne[0]["code"], request.form.get("oneonetypeone"), request.form.get("oneonetypetwo"), request.form.get("oneonetypethree"), request.form.get("oneoneueqns"), request.form.get("oneonegrade"))
        flash("Module successfully added to Y1S1!", "success")
        return redirect("/plan")
        
    # removes module to Y1S1
    elif request.method == "POST" and (request.form["btn"] == "removeoneone"):
        oneonemod = request.form.get("code")
        db.execute("DELETE FROM yearonesemone WHERE modulecode = ?", oneonemod)
        flash("Module successfully removed from Y1S1!", "success")
        return redirect("/plan")
    
    # adds modules to Y1S2
    if request.method == "POST" and (request.form["btn"] == "addonetwo"):
        
        onetwomod = request.form.get("onetwomod")
        if not onetwomod or not request.form.get("onetwoueqns") or not request.form.get("onetwograde"):
            flash("Please fill up the module code, U.E and grade in that row!", "error")
            return redirect("/plan")
        
        # checks for duplicate values
        
        typeone = request.form.get("onetwotypeone")
        typetwo = request.form.get("onetwotypetwo")
        typethree = request.form.get("onetwotypethree")
        
        # all majors
        if (typeone == "major" and typetwo == "major"):
            flash("Please dont select the same types!", "error")
            return redirect("/plan")
        
        # all second majors
        if (typeone == "majortwo" and typetwo == "majortwo") or (typeone == "majortwo" and typethree == "majortwo") or (typetwo == "majortwo" and typethree == "majortwo") or (typeone == "majortwo" and typetwo == "majortwo" and typethree == "majortwo"):
            flash("Please dont select the same types!", "error")
            return redirect("/plan")
        
        # all minorone
        if (typeone == "minorone" and typetwo == "minorone") or (typeone == "minorone" and typethree == "minorone") or (typetwo == "minorone" and typethree == "minorone") or (typeone == "minorone" and typetwo == "minorone" and typethree == "minorone"):
            flash("Please dont select the same types!", "error")
            return redirect("/plan")
        
        # all minortwo
        if (typeone == "minortwo" and typetwo == "minortwo") or (typeone == "minortwo" and typethree == "minortwo") or (typetwo == "minortwo" and typethree == "minortwo") or (typeone == "minortwo" and typetwo == "minortwo" and typethree == "minortwo"):
            flash("Please dont select the same types!", "error")
            return redirect("/plan")
        
        # all minorthree
        if (typeone == "minorthree" and typetwo == "minorthree") or (typeone == "minorthree" and typethree == "minorthree") or (typetwo == "minorthree" and typethree == "minorthree") or (typeone == "minorthree" and typetwo == "minorthree" and typethree == "minorthree"):
            flash("Please dont select the same types!", "error")
            return redirect("/plan")
        
        ModOneTwo = db.execute("SELECT * FROM Modules WHERE code = ? AND semtwo = ? AND approved = ?", onetwomod, 1, 1)
        if len(ModOneTwo) != 1:
            flash("Invalid Module Code or Module Not Avaliable in Semester 1!", "error")
            return redirect("/plan")
        
        elif ModOneTwo:
            
            DuplicateOneTwo = db.execute("SELECT * FROM yearonesemtwo WHERE modulecode = ?", ModOneTwo[0]["code"])
            
            if len(DuplicateOneTwo) == 1:
                flash("Module already in plan!", "error")
                return redirect("/plan")
        
        db.execute("INSERT INTO yearonesemtwo (planid, modulecode, typeone, typetwo, typethree, ue, grade) VALUES (?, ?, ?, ?, ?, ?, ?)", planID, ModOneTwo[0]["code"], request.form.get("onetwotypeone"), request.form.get("onetwotypetwo"), request.form.get("onetwotypethree"), request.form.get("onetwoueqns"), request.form.get("onetwograde"))
        flash("Module successfully added to Y1S2!", "success")
        return redirect("/plan")
    
    # removes module to Y1S2
    elif request.method == "POST" and (request.form["btn"] == "removeonetwo"):
        onetwomod = request.form.get("code")
        db.execute("DELETE FROM yearonesemtwo WHERE modulecode = ?", onetwomod)
        flash("Module successfully removed from Y1S2!", "success")
        return redirect("/plan")
    
    # Load year one sem one modules
    yearonesemoneDB = db.execute("SELECT * FROM yearonesemone, Modules WHERE yearonesemone.planid = ? AND modules.code=yearonesemone.modulecode", planID) 
    if len(yearonesemoneDB) >= 10:
        yOnesOnemod = 0
    else:
        yOnesOnemod = 1
        
    # Load year one sem two modules
    yearonesemtwoDB = db.execute("SELECT * FROM yearonesemtwo, Modules WHERE yearonesemtwo.planid = ? AND modules.code=yearonesemtwo.modulecode", planID) 
    if len(yearonesemtwoDB) >= 10:
        yOnesTwomod = 0
    else:
        yOnesTwomod = 1
    
    return render_template("plan.html",time=time, plan=plan, requirements=requirements, planID = planID, yOnesOnemod=yOnesOnemod, yearonesemone = yearonesemoneDB, yOnesTwomod=yOnesTwomod, yearonesemtwo = yearonesemtwoDB)


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


@app.route("/modules")
def modules():
    q = request.args.get("q")
    if q:
        modules = db.execute("SELECT * FROM Modules WHERE approved = 1 AND code LIKE ? OR name LIKE ?", "%" + str(q) + "%", "%" + str(q) + "%")
    else:
        modules = db.execute("SELECT * FROM Modules WHERE approved = 1")
    time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return render_template("modules.html", time=time, modules=modules)

if __name__ == '__main__':
    app.debug = True
    app.run()