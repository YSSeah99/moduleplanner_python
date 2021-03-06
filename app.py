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
from helpers import login_required, admin_only, load_plan_as_session, GradeScore
from secret import secretpassword

app = Flask(__name__)
app.secret_key = secretpassword
app.config["TEMPLATES_AUTO_RELOAD"] = True
#app.config["SQLALCHEMY_DATABASE_URI"] = 'postgres://suzrhvqkuoxsxx:c91b8f69ccbaaeae2f0f00b82d810b871951495de183622da342a06846ebe6d3@ec2-44-206-11-200.compute-1.amazonaws.com:5432/d2dlfdj7086r02'
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
        
            # rejects when planname not found
            else:
                flash("Please create a plan first!", "error")
                return redirect("/")
                
    # when user selects year and degree
    elif request.method == "POST" and (request.form["btn"] == "create"):
        planname = request.form.get("planname")
        planDB = db.execute("SELECT * FROM Plans")
        
        if not planname:
            flash("Please enter your matriculation number and NUSNET ID!", "error")
            return redirect("/")
        
        # check if user has already has a plan (if does prompt error, else creates)
        if len(planDB)!= 0:
            for i in range(len(planDB)):
                if (check_password_hash(planDB[i]["hashname"], planname)):
                    flash("Plan already exist! Just load the existing plan or save / update the plan.", "error")   
                    return redirect("/")
                
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
                latest = db.execute("SELECT * FROM Plans")
                db.execute("INSERT INTO Plans (id, hashname, year, degreename, spec, secondmajor, minorone, minortwo, minorthree) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (len(latest)+1), generate_password_hash(planname), year, degreeID[0]["id"], spec, secondmajor, minorone, minortwo, minorthree)
                latest = db.execute("SELECT * FROM Plans")
                planDB = db.execute("SELECT * FROM Plans WHERE id = ?", len(latest))
                db.execute("INSERT INTO specialterms (planid) VALUES (?)", planDB[0]["id"])
                flash("Plan successfully created!", "success")
                session["user_id"] = int(planDB[0]["id"]) + 500
                return redirect("/plan")
    
    # check if user has already has a plan (if does updates)  
    elif request.method == "POST" and (request.form["btn"] == "update"):
        planname = request.form.get("planname")
        planDB = db.execute("SELECT * FROM Plans")
        
        if not planname:
            flash("Please enter your matriculation number and NUSNET ID!", "error")
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
    totalDmc = requirements[0]["totalmc"]
    specialtermsDB = db.execute("SELECT * FROM specialterms WHERE planid = ?", planID)
    stOne, stTwo, stThree, stFour = specialtermsDB[0]["yearone"], specialtermsDB[0]["yeartwo"], specialtermsDB[0]["yearthree"], specialtermsDB[0]["yearfour"]
    
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
        
    # removes module from Y1S1
    elif request.method == "POST" and (request.form["btn"] == "removeoneone"):
        oneonemod = request.form.get("code")
        db.execute("DELETE FROM yearonesemone WHERE modulecode = ?", oneonemod)
        flash("Module successfully removed from Y1S1!", "success")
        return redirect("/plan")
    
    # adds modules to Y1S2
    elif request.method == "POST" and (request.form["btn"] == "addonetwo"):
        
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
            flash("Invalid Module Code or Module Not Avaliable in Semester 2!", "error")
            return redirect("/plan")
        
        elif ModOneTwo:
            
            DuplicateOneTwo = db.execute("SELECT * FROM yearonesemtwo WHERE modulecode = ?", ModOneTwo[0]["code"])
            
            if len(DuplicateOneTwo) == 1:
                flash("Module already in plan!", "error")
                return redirect("/plan")
        
        db.execute("INSERT INTO yearonesemtwo (planid, modulecode, typeone, typetwo, typethree, ue, grade) VALUES (?, ?, ?, ?, ?, ?, ?)", planID, ModOneTwo[0]["code"], request.form.get("onetwotypeone"), request.form.get("onetwotypetwo"), request.form.get("onetwotypethree"), request.form.get("onetwoueqns"), request.form.get("onetwograde"))
        flash("Module successfully added to Y1S2!", "success")
        return redirect("/plan")
    
    # removes module from Y1S2
    elif request.method == "POST" and (request.form["btn"] == "removeonetwo"):
        onetwomod = request.form.get("code")
        db.execute("DELETE FROM yearonesemtwo WHERE modulecode = ?", onetwomod)
        flash("Module successfully removed from Y1S2!", "success")
        return redirect("/plan")
    
    # adds specialterm (yearone)
    elif request.method == "POST" and (request.form["btn"] == "stOneadd"):
        db.execute("UPDATE specialterms SET yearone = 1 WHERE planid = ?", planID)
        flash("Special Term Added For Year 1 successfully!", "success")
        return redirect("/plan")
    
    # adds modules to Y1ST
    elif request.method == "POST" and (request.form["btn"] == "addonethree"):
        
        onethreemod = request.form.get("onethreemod")
        if not onethreemod or not request.form.get("onethreeueqns") or not request.form.get("onethreegrade"):
            flash("Please fill up the module code, U.E and grade in that row!", "error")
            return redirect("/plan")
        
        # checks for duplicate values
        
        typeone = request.form.get("onethreetypeone")
        typetwo = request.form.get("onethreetypetwo")
        typethree = request.form.get("onethreetypethree")
        
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
        
        ModOneThree = db.execute("SELECT * FROM Modules WHERE code = ? AND semthree = ? OR semfour = ? AND approved = ?", onethreemod, 1, 1, 1)
        if len(ModOneThree) != 1:
            flash("Invalid Module Code or Module Not Avaliable in Special Term!", "error")
            return redirect("/plan")
        
        elif ModOneThree:
            
            DuplicateOneThree = db.execute("SELECT * FROM yearonespecialterm WHERE modulecode = ?", ModOneThree[0]["code"])
            
            if len(DuplicateOneThree) == 1:
                flash("Module already in plan!", "error")
                return redirect("/plan")
        
        db.execute("INSERT INTO yearonespecialterm (planid, modulecode, typeone, typetwo, typethree, ue, grade) VALUES (?, ?, ?, ?, ?, ?, ?)", planID, ModOneThree[0]["code"], request.form.get("onethreetypeone"), request.form.get("onethreetypetwo"), request.form.get("onethreetypethree"), request.form.get("onethreeueqns"), request.form.get("onethreegrade"))
        flash("Module successfully added to Y1ST!", "success")
        return redirect("/plan")
    
    # removes modules from Y1ST
    elif request.method == "POST" and (request.form["btn"] == "removeonethree"):
        onethreemod = request.form.get("code")
        db.execute("DELETE FROM yearonespecialterm WHERE modulecode = ?", onethreemod)
        flash("Module successfully removed from Y1 Special Term!", "success")
        return redirect("/plan")
    
    # removes specialterm (yearone)
    elif request.method == "POST" and (request.form["btn"] == "stOneremove"):
        db.execute("UPDATE specialterms SET yearone = 0 WHERE planid = ?", planID)
        flash("Special Term Removed For Year 1 successfully!", "success")
        return redirect("/plan")
    
    # adds modules to Y2S1
    elif request.method == "POST" and (request.form["btn"] == "addtwoone"):
        
        twoonemod = request.form.get("twoonemod")
        if not twoonemod or not request.form.get("twooneueqns") or not request.form.get("twoonegrade"):
            flash("Please fill up the module code, U.E and grade in that row!", "error")
            return redirect("/plan")
        
        # checks for duplicate values
        
        typeone = request.form.get("twoonetypeone")
        typetwo = request.form.get("twoonetypetwo")
        typethree = request.form.get("twoonetypethree")
        
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
        
        ModTwoOne = db.execute("SELECT * FROM Modules WHERE code = ? AND semone = ? AND approved = ?", twoonemod, 1, 1)
        if len(ModTwoOne) != 1:
            flash("Invalid Module Code or Module Not Avaliable in Semester 1!", "error")
            return redirect("/plan")
        
        elif ModTwoOne:
            
            DuplicateTwoOne = db.execute("SELECT * FROM yeartwosemone WHERE modulecode = ?", ModTwoOne[0]["code"])
            
            if len(DuplicateTwoOne) == 1:
                flash("Module already in plan!", "error")
                return redirect("/plan")
        
        db.execute("INSERT INTO yeartwosemone (planid, modulecode, typeone, typetwo, typethree, ue, grade) VALUES (?, ?, ?, ?, ?, ?, ?)", planID, ModTwoOne[0]["code"], typeone, typetwo, typethree, request.form.get("twooneueqns"), request.form.get("twoonegrade"))
        flash("Module successfully added to Y2S1!", "success")
        return redirect("/plan")
        
    # removes module from Y2S1
    elif request.method == "POST" and (request.form["btn"] == "removetwoone"):
        twoonemod = request.form.get("code")
        db.execute("DELETE FROM yeartwosemone WHERE modulecode = ?", twoonemod)
        flash("Module successfully removed from Y2S1!", "success")
        return redirect("/plan")
    
    # adds modules to Y2S2
    elif request.method == "POST" and (request.form["btn"] == "addtwotwo"):
        
        twotwomod = request.form.get("twotwomod")
        if not twotwomod or not request.form.get("twotwoueqns") or not request.form.get("twotwograde"):
            flash("Please fill up the module code, U.E and grade in that row!", "error")
            return redirect("/plan")
        
        # checks for duplicate values
        
        typeone = request.form.get("twotwotypeone")
        typetwo = request.form.get("twotwotypetwo")
        typethree = request.form.get("twotwotypethree")
        
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
        
        ModTwoTwo = db.execute("SELECT * FROM Modules WHERE code = ? AND semtwo = ? AND approved = ?", twotwomod, 1, 1)
        if len(ModTwoTwo) != 1:
            flash("Invalid Module Code or Module Not Avaliable in Semester 2!", "error")
            return redirect("/plan")
        
        elif ModTwoTwo:
            
            DuplicateTwoTwo = db.execute("SELECT * FROM yeartwosemtwo WHERE modulecode = ?", ModTwoTwo[0]["code"])
            
            if len(DuplicateTwoTwo) == 1:
                flash("Module already in plan!", "error")
                return redirect("/plan")
        
        db.execute("INSERT INTO yeartwosemtwo (planid, modulecode, typeone, typetwo, typethree, ue, grade) VALUES (?, ?, ?, ?, ?, ?, ?)", planID, ModTwoTwo[0]["code"], typeone, typetwo, typethree, request.form.get("twotwoueqns"), request.form.get("twotwograde"))
        flash("Module successfully added to Y2S2!", "success")
        return redirect("/plan")
    
    # removes module from Y2S2
    elif request.method == "POST" and (request.form["btn"] == "removetwotwo"):
        twotwomod = request.form.get("code")
        db.execute("DELETE FROM yeartwosemtwo WHERE modulecode = ?", twotwomod)
        flash("Module successfully removed from Y2S2!", "success")
        return redirect("/plan")
    
    # adds specialterm (Y2)
    elif request.method == "POST" and (request.form["btn"] == "stTwoadd"):
        db.execute("UPDATE specialterms SET yeartwo = 1 WHERE planid = ?", planID)
        flash("Special Term Added For Year 2 successfully!", "success")
        return redirect("/plan")
    
    # adds modules to Y2ST
    elif request.method == "POST" and (request.form["btn"] == "addtwothree"):
        
        twothreemod = request.form.get("twothreemod")
        if not twothreemod or not request.form.get("twothreeueqns") or not request.form.get("twothreegrade"):
            flash("Please fill up the module code, U.E and grade in that row!", "error")
            return redirect("/plan")
        
        # checks for duplicate values
        
        typeone = request.form.get("twothreetypeone")
        typetwo = request.form.get("twothreetypetwo")
        typethree = request.form.get("twothreetypethree")
        
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
        
        ModTwoThree = db.execute("SELECT * FROM Modules WHERE code = ? AND semthree = ? OR semfour = ? AND approved = ?", twothreemod, 1, 1, 1)
        if len(ModTwoThree) != 1:
            flash("Invalid Module Code or Module Not Avaliable in Special Term!", "error")
            return redirect("/plan")
        
        elif ModTwoThree:
            
            DuplicateTwoThree = db.execute("SELECT * FROM yeartwospecialterm WHERE modulecode = ?", ModTwoThree[0]["code"])
            
            if len(DuplicateTwoThree) == 1:
                flash("Module already in plan!", "error")
                return redirect("/plan")
        
        db.execute("INSERT INTO yeartwospecialterm (planid, modulecode, typeone, typetwo, typethree, ue, grade) VALUES (?, ?, ?, ?, ?, ?, ?)", planID, ModTwoThree[0]["code"], typeone, typetwo, typethree, request.form.get("twothreeueqns"), request.form.get("twothreegrade"))
        flash("Module successfully added to Y2ST!", "success")
        return redirect("/plan")
    
    # removes modules from Y2ST
    elif request.method == "POST" and (request.form["btn"] == "removetwothree"):
        twothreemod = request.form.get("code")
        db.execute("DELETE FROM yeartwospecialterm WHERE modulecode = ?", twothreemod)
        flash("Module successfully removed from Y2 Special Term!", "success")
        return redirect("/plan")
    
    # removes specialterm (yeartwo)
    elif request.method == "POST" and (request.form["btn"] == "stTworemove"):
        db.execute("UPDATE specialterms SET yeartwo = 0 WHERE planid = ?", planID)
        flash("Special Term Removed For Year 2 successfully!", "success")
        return redirect("/plan")
    
    # adds modules to Y3S1
    elif request.method == "POST" and (request.form["btn"] == "addthreeone"):
        
        threeonemod = request.form.get("threeonemod")
        if not threeonemod or not request.form.get("threeoneueqns") or not request.form.get("threeonegrade"):
            flash("Please fill up the module code, U.E and grade in that row!", "error")
            return redirect("/plan")
        
        # checks for duplicate values
        
        typeone = request.form.get("threeonetypeone")
        typetwo = request.form.get("threeonetypetwo")
        typethree = request.form.get("threeonetypethree")
        
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
        
        ModThreeOne = db.execute("SELECT * FROM Modules WHERE code = ? AND semone = ? AND approved = ?", threeonemod, 1, 1)
        if len(ModThreeOne) != 1:
            flash("Invalid Module Code or Module Not Avaliable in Semester 1!", "error")
            return redirect("/plan")
        
        elif ModThreeOne:
            
            DuplicateThreeOne = db.execute("SELECT * FROM yearthreesemone WHERE modulecode = ?", ModThreeOne[0]["code"])
            
            if len(DuplicateThreeOne) == 1:
                flash("Module already in plan!", "error")
                return redirect("/plan")
        
        db.execute("INSERT INTO yearthreesemone (planid, modulecode, typeone, typetwo, typethree, ue, grade) VALUES (?, ?, ?, ?, ?, ?, ?)", planID, ModThreeOne[0]["code"], typeone, typetwo, typethree, request.form.get("threeoneueqns"), request.form.get("threeonegrade"))
        flash("Module successfully added to Y3S1!", "success")
        return redirect("/plan")
        
    # removes module from Y3S1
    elif request.method == "POST" and (request.form["btn"] == "removethreeone"):
        threeonemod = request.form.get("code")
        db.execute("DELETE FROM yearthreesemone WHERE modulecode = ?", threeonemod)
        flash("Module successfully removed from Y3S1!", "success")
        return redirect("/plan")
    
    # adds modules to Y3S2
    elif request.method == "POST" and (request.form["btn"] == "addthreetwo"):
        
        threetwomod = request.form.get("threetwomod")
        if not threetwomod or not request.form.get("threetwoueqns") or not request.form.get("threetwograde"):
            flash("Please fill up the module code, U.E and grade in that row!", "error")
            return redirect("/plan")
        
        # checks for duplicate values
        
        typeone = request.form.get("threetwotypeone")
        typetwo = request.form.get("threetwotypetwo")
        typethree = request.form.get("threetwotypethree")
        
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
        
        ModThreeTwo = db.execute("SELECT * FROM Modules WHERE code = ? AND semtwo = ? AND approved = ?", threetwomod, 1, 1)
        if len(ModThreeTwo) != 1:
            flash("Invalid Module Code or Module Not Avaliable in Semester 2!", "error")
            return redirect("/plan")
        
        elif ModThreeTwo:
            
            DuplicateThreeTwo = db.execute("SELECT * FROM yearthreesemtwo WHERE modulecode = ?", ModThreeTwo[0]["code"])
            
            if len(DuplicateThreeTwo) == 1:
                flash("Module already in plan!", "error")
                return redirect("/plan")
        
        db.execute("INSERT INTO yearthreesemtwo (planid, modulecode, typeone, typetwo, typethree, ue, grade) VALUES (?, ?, ?, ?, ?, ?, ?)", planID, ModThreeTwo[0]["code"], typeone, typetwo, typethree, request.form.get("threetwoueqns"), request.form.get("threetwograde"))
        flash("Module successfully added to Y3S2!", "success")
        return redirect("/plan")
    
    # removes module from Y3S2
    elif request.method == "POST" and (request.form["btn"] == "removethreetwo"):
        threetwomod = request.form.get("code")
        db.execute("DELETE FROM yearthreesemtwo WHERE modulecode = ?", threetwomod)
        flash("Module successfully removed from Y3S2!", "success")
        return redirect("/plan")
    
    # adds specialterm (Y3)
    elif request.method == "POST" and (request.form["btn"] == "stThreeadd"):
        db.execute("UPDATE specialterms SET yearthree = 1 WHERE planid = ?", planID)
        flash("Special Term Added For Year 3 successfully!", "success")
        return redirect("/plan")
    
    # adds modules to Y3ST
    elif request.method == "POST" and (request.form["btn"] == "addthreethree"):
        
        threethreemod = request.form.get("threethreemod")
        if not threethreemod or not request.form.get("threethreeueqns") or not request.form.get("threethreegrade"):
            flash("Please fill up the module code, U.E and grade in that row!", "error")
            return redirect("/plan")
        
        # checks for duplicate values
        
        typeone = request.form.get("threethreetypeone")
        typetwo = request.form.get("threethreetypetwo")
        typethree = request.form.get("threethreetypethree")
        
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
        
        ModThreeThree = db.execute("SELECT * FROM Modules WHERE code = ? AND semthree = ? OR semfour = ? AND approved = ?", threethreemod, 1, 1, 1)
        if len(ModThreeThree) != 1:
            flash("Invalid Module Code or Module Not Avaliable in Special Term!", "error")
            return redirect("/plan")
        
        elif ModThreeThree:
            
            DuplicateThreeThree = db.execute("SELECT * FROM yearthreespecialterm WHERE modulecode = ?", ModThreeThree[0]["code"])
            
            if len(DuplicateThreeThree) == 1:
                flash("Module already in plan!", "error")
                return redirect("/plan")
        
        db.execute("INSERT INTO yearthreespecialterm (planid, modulecode, typeone, typetwo, typethree, ue, grade) VALUES (?, ?, ?, ?, ?, ?, ?)", planID, ModThreeThree[0]["code"], typeone, typetwo, typethree, request.form.get("threethreeueqns"), request.form.get("threethreegrade"))
        flash("Module successfully added to Y3ST!", "success")
        return redirect("/plan")
    
    # removes modules from Y3ST
    elif request.method == "POST" and (request.form["btn"] == "removethreethree"):
        threethreemod = request.form.get("code")
        db.execute("DELETE FROM yearthreespecialterm WHERE modulecode = ?", threethreemod)
        flash("Module successfully removed from Y3 Special Term!", "success")
        return redirect("/plan")
    
    # removes specialterm (year3)
    elif request.method == "POST" and (request.form["btn"] == "stThreeremove"):
        db.execute("UPDATE specialterms SET yearthree = 0 WHERE planid = ?", planID)
        flash("Special Term Removed For Year 3 successfully!", "success")
        return redirect("/plan")
    
    # adds modules to Y4S1
    elif request.method == "POST" and (request.form["btn"] == "addfourone"):
        
        fouronemod = request.form.get("fouronemod")
        if not fouronemod or not request.form.get("fouroneueqns") or not request.form.get("fouronegrade"):
            flash("Please fill up the module code, U.E and grade in that row!", "error")
            return redirect("/plan")
        
        # checks for duplicate values
        
        typeone = request.form.get("fouronetypeone")
        typetwo = request.form.get("fouronetypetwo")
        typethree = request.form.get("fouronetypethree")
        
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
        
        ModFourOne = db.execute("SELECT * FROM Modules WHERE code = ? AND semone = ? AND approved = ?", fouronemod, 1, 1)
        if len(ModFourOne) != 1:
            flash("Invalid Module Code or Module Not Avaliable in Semester 1!", "error")
            return redirect("/plan")
        
        elif ModFourOne:
            
            DuplicateFourOne = db.execute("SELECT * FROM yearfoursemone WHERE modulecode = ?", ModFourOne[0]["code"])
            
            if len(DuplicateFourOne) == 1:
                flash("Module already in plan!", "error")
                return redirect("/plan")
        
        db.execute("INSERT INTO yearfoursemone (planid, modulecode, typeone, typetwo, typethree, ue, grade) VALUES (?, ?, ?, ?, ?, ?, ?)", planID, ModFourOne[0]["code"], typeone, typetwo, typethree, request.form.get("fouroneueqns"), request.form.get("fouronegrade"))
        flash("Module successfully added to Y4S1!", "success")
        return redirect("/plan")
        
    # removes module from Y4S1
    elif request.method == "POST" and (request.form["btn"] == "removefourone"):
        fouronemod = request.form.get("code")
        db.execute("DELETE FROM yearfoursemone WHERE modulecode = ?", fouronemod)
        flash("Module successfully removed from Y4S1!", "success")
        return redirect("/plan")
    
    # adds modules to Y3S2
    elif request.method == "POST" and (request.form["btn"] == "addfourtwo"):
        
        fourtwomod = request.form.get("fourtwomod")
        if not fourtwomod or not request.form.get("fourtwoueqns") or not request.form.get("fourtwograde"):
            flash("Please fill up the module code, U.E and grade in that row!", "error")
            return redirect("/plan")
        
        # checks for duplicate values
        
        typeone = request.form.get("fourtwotypeone")
        typetwo = request.form.get("fourtwotypetwo")
        typethree = request.form.get("fourtwotypethree")
        
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
        
        ModFourTwo = db.execute("SELECT * FROM Modules WHERE code = ? AND semtwo = ? AND approved = ?", fourtwomod, 1, 1)
        if len(ModFourTwo) != 1:
            flash("Invalid Module Code or Module Not Avaliable in Semester 2!", "error")
            return redirect("/plan")
        
        elif ModFourTwo:
            
            DuplicateFourTwo = db.execute("SELECT * FROM yearfoursemtwo WHERE modulecode = ?", ModFourTwo[0]["code"])
            
            if len(DuplicateFourTwo) == 1:
                flash("Module already in plan!", "error")
                return redirect("/plan")
        
        db.execute("INSERT INTO yearfoursemtwo (planid, modulecode, typeone, typetwo, typethree, ue, grade) VALUES (?, ?, ?, ?, ?, ?, ?)", planID, ModFourTwo[0]["code"], typeone, typetwo, typethree, request.form.get("fourtwoueqns"), request.form.get("fourtwograde"))
        flash("Module successfully added to Y4S2!", "success")
        return redirect("/plan")
    
    # removes module from Y4S2
    elif request.method == "POST" and (request.form["btn"] == "removefourtwo"):
        fourtwomod = request.form.get("code")
        db.execute("DELETE FROM yearfoursemtwo WHERE modulecode = ?", fourtwomod)
        flash("Module successfully removed from Y4S2!", "success")
        return redirect("/plan")
    
    # adds specialterm (Y4)
    elif request.method == "POST" and (request.form["btn"] == "stFouradd"):
        db.execute("UPDATE specialterms SET yearfour = 1 WHERE planid = ?", planID)
        flash("Special Term Added For Year 4 successfully!", "success")
        return redirect("/plan")
    
    # adds modules to Y4ST
    elif request.method == "POST" and (request.form["btn"] == "addfourthree"):
        
        fourthreemod = request.form.get("fourthreemod")
        if not fourthreemod or not request.form.get("fourthreeueqns") or not request.form.get("fourthreegrade"):
            flash("Please fill up the module code, U.E and grade in that row!", "error")
            return redirect("/plan")
        
        # checks for duplicate values
        
        typeone = request.form.get("fourthreetypeone")
        typetwo = request.form.get("fourthreetypetwo")
        typethree = request.form.get("fourthreetypethree")
        
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
        
        ModFourThree = db.execute("SELECT * FROM Modules WHERE code = ? AND semthree = ? OR semfour = ? AND approved = ?", fourthreemod, 1, 1, 1)
        if len(ModFourThree) != 1:
            flash("Invalid Module Code or Module Not Avaliable in Special Term!", "error")
            return redirect("/plan")
        
        elif ModFourThree:
            
            DuplicateFourThree = db.execute("SELECT * FROM yearfourspecialterm WHERE modulecode = ?", ModFourThree[0]["code"])
            
            if len(DuplicateFourThree) == 1:
                flash("Module already in plan!", "error")
                return redirect("/plan")
        
        db.execute("INSERT INTO yearfourspecialterm (planid, modulecode, typeone, typetwo, typethree, ue, grade) VALUES (?, ?, ?, ?, ?, ?, ?)", planID, ModFourThree[0]["code"], typeone, typetwo, typethree, request.form.get("fourthreeueqns"), request.form.get("fourthreegrade"))
        flash("Module successfully added to Y4ST!", "success")
        return redirect("/plan")
    
    # removes modules from Y4ST
    elif request.method == "POST" and (request.form["btn"] == "removefourthree"):
        fourthreemod = request.form.get("code")
        db.execute("DELETE FROM yearfourspecialterm WHERE modulecode = ?", fourthreemod)
        flash("Module successfully removed from Y4 Special Term!", "success")
        return redirect("/plan")
    
    # removes specialterm (year4)
    elif request.method == "POST" and (request.form["btn"] == "stFourremove"):
        db.execute("UPDATE specialterms SET yearfour = 0 WHERE planid = ?", planID)
        flash("Special Term Removed For Year 4 successfully!", "success")
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
    
    # Loads year one specialterm
    yearoneSTDB = db.execute("SELECT * FROM yearonespecialterm, Modules WHERE yearonespecialterm.planid = ? AND modules.code=yearonespecialterm.modulecode", planID)    
    if len(yearoneSTDB) >= 5:
        yOnesThreemod = 0
    else:
        yOnesThreemod = 1
        
    # Load year two sem one modules
    yeartwosemoneDB = db.execute("SELECT * FROM yeartwosemone, Modules WHERE yeartwosemone.planid = ? AND modules.code=yeartwosemone.modulecode", planID) 
    if len(yeartwosemoneDB) >= 10:
        yTwosOnemod = 0
    else:
        yTwosOnemod = 1
        
    # Load year two sem two modules
    yeartwosemtwoDB = db.execute("SELECT * FROM yeartwosemtwo, Modules WHERE yeartwosemtwo.planid = ? AND modules.code=yeartwosemtwo.modulecode", planID) 
    if len(yeartwosemtwoDB) >= 10:
        yTwosTwomod = 0
    else:
        yTwosTwomod = 1
    
    # Loads year two specialterm
    yeartwoSTDB = db.execute("SELECT * FROM yeartwospecialterm, Modules WHERE yeartwospecialterm.planid = ? AND modules.code=yeartwospecialterm.modulecode", planID)    
    if len(yeartwoSTDB) >= 5:
        yTwosThreemod = 0
    else:
        yTwosThreemod = 1
        
    # Load year three sem one modules
    yearthreesemoneDB = db.execute("SELECT * FROM yearthreesemone, Modules WHERE yearthreesemone.planid = ? AND modules.code=yearthreesemone.modulecode", planID) 
    if len(yearthreesemoneDB) >= 10:
        yThreesOnemod = 0
    else:
        yThreesOnemod = 1
        
    # Load year three sem two modules
    yearthreesemtwoDB = db.execute("SELECT * FROM yearthreesemtwo, Modules WHERE yearthreesemtwo.planid = ? AND modules.code=yearthreesemtwo.modulecode", planID) 
    if len(yearthreesemtwoDB) >= 10:
        yThreesTwomod = 0
    else:
        yThreesTwomod = 1
    
    # Loads year three specialterm
    yearthreeSTDB = db.execute("SELECT * FROM yearthreespecialterm, Modules WHERE yearthreespecialterm.planid = ? AND modules.code=yearthreespecialterm.modulecode", planID)    
    if len(yearthreeSTDB) >= 5:
        yThreesThreemod = 0
    else:
        yThreesThreemod = 1
        
    # Load year four sem one modules
    yearfoursemoneDB = db.execute("SELECT * FROM yearfoursemone, Modules WHERE yearfoursemone.planid = ? AND modules.code=yearfoursemone.modulecode", planID) 
    if len(yearfoursemoneDB) >= 10:
        yFoursOnemod = 0
    else:
        yFoursOnemod = 1
        
    # Load year four sem two modules
    yearfoursemtwoDB = db.execute("SELECT * FROM yearfoursemtwo, Modules WHERE yearfoursemtwo.planid = ? AND modules.code=yearfoursemtwo.modulecode", planID) 
    if len(yearfoursemtwoDB) >= 10:
        yFoursTwomod = 0
    else:
        yFoursTwomod = 1
    
    # Loads year three specialterm
    yearfourSTDB = db.execute("SELECT * FROM yearfourspecialterm, Modules WHERE yearfourspecialterm.planid = ? AND modules.code=yearfourspecialterm.modulecode", planID)    
    if len(yearfourSTDB) >= 5:
        yFoursThreemod = 0
    else:
        yFoursThreemod = 1
    
    # calculations shit
    cap, sumc, score, totalmc, unimc, facmc, majormc, specmc, majortwomc, minoronemc, minortwomc, minorthreemc, uemc = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    
    # for Y1S1
    for mod in yearonesemoneDB:
        totalmc += int(mod["mc"])
        if mod["grade"] == "S" or mod["grade"] == "U" or mod["grade"] == "NIL":
            sumc += int(mod["mc"])
        else:
            score += GradeScore(mod["grade"], int(mod["mc"]))
        if mod["ue"] == 1: 
            uemc += int(mod["mc"])   
        if mod["typeone"] == "uni": 
            unimc += int(mod["mc"]) 
        if mod["typeone"] == "fac": 
            facmc += int(mod["mc"])
        if mod["typetwo"] == "spec": 
            specmc += int(mod["mc"])
        if mod["typeone"] == "major" or mod["typetwo"] == "major": 
            majormc += int(mod["mc"])
        if mod["typeone"] == "majortwo" or mod["typetwo"] == "majortwo" or mod["typethree"] == "majortwo": 
            majortwomc += int(mod["mc"])
        if mod["typeone"] == "minorone" or mod["typetwo"] == "minorone" or mod["typethree"] == "minorone": 
            minoronemc += int(mod["mc"]) 
        if mod["typeone"] == "minortwo" or mod["typetwo"] == "minortwo" or mod["typethree"] == "minortwo": 
            minortwomc += int(mod["mc"]) 
        if mod["typeone"] == "minorthree" or mod["typetwo"] == "minorthree" or mod["typethree"] == "minorthree": 
            minorthreemc += int(mod["mc"])
            
    # for Y1S2
    for mod in yearonesemtwoDB:
        totalmc += int(mod["mc"])
        if mod["grade"] == "S" or mod["grade"] == "U" or mod["grade"] == "NIL":
            sumc += int(mod["mc"])
        else:
            score += GradeScore(mod["grade"], int(mod["mc"]))
        if mod["ue"] == 1: 
            uemc += int(mod["mc"])   
        if mod["typeone"] == "uni": 
            unimc += int(mod["mc"]) 
        if mod["typeone"] == "fac": 
            facmc += int(mod["mc"])
        if mod["typetwo"] == "spec": 
            specmc += int(mod["mc"])
        if mod["typeone"] == "major" or mod["typetwo"] == "major": 
            majormc += int(mod["mc"])
        if mod["typeone"] == "majortwo" or mod["typetwo"] == "majortwo" or mod["typethree"] == "majortwo": 
            majortwomc += int(mod["mc"])
        if mod["typeone"] == "minorone" or mod["typetwo"] == "minorone" or mod["typethree"] == "minorone": 
            minoronemc += int(mod["mc"]) 
        if mod["typeone"] == "minortwo" or mod["typetwo"] == "minortwo" or mod["typethree"] == "minortwo": 
            minortwomc += int(mod["mc"]) 
        if mod["typeone"] == "minorthree" or mod["typetwo"] == "minorthree" or mod["typethree"] == "minorthree": 
            minorthreemc += int(mod["mc"])  
    
    # for Y1ST
    if len(yearoneSTDB) != 0:
        for mod in yearoneSTDB:
            totalmc += int(mod["mc"])
            if mod["grade"] == "S" or mod["grade"] == "U" or mod["grade"] == "NIL":
                sumc += int(mod["mc"])
            else:
                score += GradeScore(mod["grade"], int(mod["mc"]))
            if mod["ue"] == 1: 
                uemc += int(mod["mc"])   
            if mod["typeone"] == "uni": 
                unimc += int(mod["mc"]) 
            if mod["typeone"] == "fac": 
                facmc += int(mod["mc"])
            if mod["typetwo"] == "spec": 
                specmc += int(mod["mc"])
            if mod["typeone"] == "major" or mod["typetwo"] == "major": 
                majormc += int(mod["mc"])
            if mod["typeone"] == "majortwo" or mod["typetwo"] == "majortwo" or mod["typethree"] == "majortwo": 
                majortwomc += int(mod["mc"])
            if mod["typeone"] == "minorone" or mod["typetwo"] == "minorone" or mod["typethree"] == "minorone": 
                minoronemc += int(mod["mc"]) 
            if mod["typeone"] == "minortwo" or mod["typetwo"] == "minortwo" or mod["typethree"] == "minortwo": 
                minortwomc += int(mod["mc"]) 
            if mod["typeone"] == "minorthree" or mod["typetwo"] == "minorthree" or mod["typethree"] == "minorthree": 
                minorthreemc += int(mod["mc"]) 
        
    # for Y2S1
    for mod in yeartwosemoneDB:
        totalmc += int(mod["mc"])
        if mod["grade"] == "S" or mod["grade"] == "U" or mod["grade"] == "NIL":
            sumc += int(mod["mc"])
        else:
            score += GradeScore(mod["grade"], int(mod["mc"]))
        if mod["ue"] == 1: 
            uemc += int(mod["mc"])   
        if mod["typeone"] == "uni": 
            unimc += int(mod["mc"]) 
        if mod["typeone"] == "fac": 
            facmc += int(mod["mc"])
        if mod["typetwo"] == "spec": 
            specmc += int(mod["mc"])
        if mod["typeone"] == "major" or mod["typetwo"] == "major": 
            majormc += int(mod["mc"])
        if mod["typeone"] == "majortwo" or mod["typetwo"] == "majortwo" or mod["typethree"] == "majortwo": 
            majortwomc += int(mod["mc"])
        if mod["typeone"] == "minorone" or mod["typetwo"] == "minorone" or mod["typethree"] == "minorone": 
            minoronemc += int(mod["mc"]) 
        if mod["typeone"] == "minortwo" or mod["typetwo"] == "minortwo" or mod["typethree"] == "minortwo": 
            minortwomc += int(mod["mc"]) 
        if mod["typeone"] == "minorthree" or mod["typetwo"] == "minorthree" or mod["typethree"] == "minorthree": 
            minorthreemc += int(mod["mc"])
            
    # for Y2S2
    for mod in yeartwosemtwoDB:
        totalmc += int(mod["mc"])
        if mod["grade"] == "S" or mod["grade"] == "U" or mod["grade"] == "NIL":
            sumc += int(mod["mc"])
        else:
            score += GradeScore(mod["grade"], int(mod["mc"]))
        if mod["ue"] == 1: 
            uemc += int(mod["mc"])   
        if mod["typeone"] == "uni": 
            unimc += int(mod["mc"]) 
        if mod["typeone"] == "fac": 
            facmc += int(mod["mc"])
        if mod["typetwo"] == "spec": 
            specmc += int(mod["mc"])
        if mod["typeone"] == "major" or mod["typetwo"] == "major": 
            majormc += int(mod["mc"])
        if mod["typeone"] == "majortwo" or mod["typetwo"] == "majortwo" or mod["typethree"] == "majortwo": 
            majortwomc += int(mod["mc"])
        if mod["typeone"] == "minorone" or mod["typetwo"] == "minorone" or mod["typethree"] == "minorone": 
            minoronemc += int(mod["mc"]) 
        if mod["typeone"] == "minortwo" or mod["typetwo"] == "minortwo" or mod["typethree"] == "minortwo": 
            minortwomc += int(mod["mc"]) 
        if mod["typeone"] == "minorthree" or mod["typetwo"] == "minorthree" or mod["typethree"] == "minorthree": 
            minorthreemc += int(mod["mc"])  
    
    # for Y2ST
    if len(yeartwoSTDB) != 0:
        for mod in yeartwoSTDB:
            totalmc += int(mod["mc"])
            if mod["grade"] == "S" or mod["grade"] == "U" or mod["grade"] == "NIL":
                sumc += int(mod["mc"])
            else:
                score += GradeScore(mod["grade"], int(mod["mc"]))
            if mod["ue"] == 1: 
                uemc += int(mod["mc"])   
            if mod["typeone"] == "uni": 
                unimc += int(mod["mc"]) 
            if mod["typeone"] == "fac": 
                facmc += int(mod["mc"])
            if mod["typetwo"] == "spec": 
                specmc += int(mod["mc"])
            if mod["typeone"] == "major" or mod["typetwo"] == "major": 
                majormc += int(mod["mc"])
            if mod["typeone"] == "majortwo" or mod["typetwo"] == "majortwo" or mod["typethree"] == "majortwo": 
                majortwomc += int(mod["mc"])
            if mod["typeone"] == "minorone" or mod["typetwo"] == "minorone" or mod["typethree"] == "minorone": 
                minoronemc += int(mod["mc"]) 
            if mod["typeone"] == "minortwo" or mod["typetwo"] == "minortwo" or mod["typethree"] == "minortwo": 
                minortwomc += int(mod["mc"]) 
            if mod["typeone"] == "minorthree" or mod["typetwo"] == "minorthree" or mod["typethree"] == "minorthree": 
                minorthreemc += int(mod["mc"]) 
          
    # for Y3S1
    for mod in yearthreesemoneDB:
        totalmc += int(mod["mc"])
        if mod["grade"] == "S" or mod["grade"] == "U" or mod["grade"] == "NIL":
            sumc += int(mod["mc"])
        else:
            score += GradeScore(mod["grade"], int(mod["mc"]))
        if mod["ue"] == 1: 
            uemc += int(mod["mc"])   
        if mod["typeone"] == "uni": 
            unimc += int(mod["mc"]) 
        if mod["typeone"] == "fac": 
            facmc += int(mod["mc"])
        if mod["typetwo"] == "spec": 
            specmc += int(mod["mc"])
        if mod["typeone"] == "major" or mod["typetwo"] == "major": 
            majormc += int(mod["mc"])
        if mod["typeone"] == "majortwo" or mod["typetwo"] == "majortwo" or mod["typethree"] == "majortwo": 
            majortwomc += int(mod["mc"])
        if mod["typeone"] == "minorone" or mod["typetwo"] == "minorone" or mod["typethree"] == "minorone": 
            minoronemc += int(mod["mc"]) 
        if mod["typeone"] == "minortwo" or mod["typetwo"] == "minortwo" or mod["typethree"] == "minortwo": 
            minortwomc += int(mod["mc"]) 
        if mod["typeone"] == "minorthree" or mod["typetwo"] == "minorthree" or mod["typethree"] == "minorthree": 
            minorthreemc += int(mod["mc"])
            
    # for Y3S2
    for mod in yearthreesemtwoDB:
        totalmc += int(mod["mc"])
        if mod["grade"] == "S" or mod["grade"] == "U" or mod["grade"] == "NIL":
            sumc += int(mod["mc"])
        else:
            score += GradeScore(mod["grade"], int(mod["mc"]))
        if mod["ue"] == 1: 
            uemc += int(mod["mc"])   
        if mod["typeone"] == "uni": 
            unimc += int(mod["mc"]) 
        if mod["typeone"] == "fac": 
            facmc += int(mod["mc"])
        if mod["typetwo"] == "spec": 
            specmc += int(mod["mc"])
        if mod["typeone"] == "major" or mod["typetwo"] == "major": 
            majormc += int(mod["mc"])
        if mod["typeone"] == "majortwo" or mod["typetwo"] == "majortwo" or mod["typethree"] == "majortwo": 
            majortwomc += int(mod["mc"])
        if mod["typeone"] == "minorone" or mod["typetwo"] == "minorone" or mod["typethree"] == "minorone": 
            minoronemc += int(mod["mc"]) 
        if mod["typeone"] == "minortwo" or mod["typetwo"] == "minortwo" or mod["typethree"] == "minortwo": 
            minortwomc += int(mod["mc"]) 
        if mod["typeone"] == "minorthree" or mod["typetwo"] == "minorthree" or mod["typethree"] == "minorthree": 
            minorthreemc += int(mod["mc"])  
    
    # for Y3ST
    if len(yearthreeSTDB) != 0:
        for mod in yearthreeSTDB:
            totalmc += int(mod["mc"])
            if mod["grade"] == "S" or mod["grade"] == "U" or mod["grade"] == "NIL":
                sumc += int(mod["mc"])
            else:
                score += GradeScore(mod["grade"], int(mod["mc"]))
            if mod["ue"] == 1: 
                uemc += int(mod["mc"])   
            if mod["typeone"] == "uni": 
                unimc += int(mod["mc"]) 
            if mod["typeone"] == "fac": 
                facmc += int(mod["mc"])
            if mod["typetwo"] == "spec": 
                specmc += int(mod["mc"])
            if mod["typeone"] == "major" or mod["typetwo"] == "major": 
                majormc += int(mod["mc"])
            if mod["typeone"] == "majortwo" or mod["typetwo"] == "majortwo" or mod["typethree"] == "majortwo": 
                majortwomc += int(mod["mc"])
            if mod["typeone"] == "minorone" or mod["typetwo"] == "minorone" or mod["typethree"] == "minorone": 
                minoronemc += int(mod["mc"]) 
            if mod["typeone"] == "minortwo" or mod["typetwo"] == "minortwo" or mod["typethree"] == "minortwo": 
                minortwomc += int(mod["mc"]) 
            if mod["typeone"] == "minorthree" or mod["typetwo"] == "minorthree" or mod["typethree"] == "minorthree": 
                minorthreemc += int(mod["mc"]) 
    
    # for Y4S1
    for mod in yearfoursemoneDB:
        totalmc += int(mod["mc"])
        if mod["grade"] == "S" or mod["grade"] == "U" or mod["grade"] == "NIL":
            sumc += int(mod["mc"])
        else:
            score += GradeScore(mod["grade"], int(mod["mc"]))
        if mod["ue"] == 1: 
            uemc += int(mod["mc"])   
        if mod["typeone"] == "uni": 
            unimc += int(mod["mc"]) 
        if mod["typeone"] == "fac": 
            facmc += int(mod["mc"])
        if mod["typetwo"] == "spec": 
            specmc += int(mod["mc"])
        if mod["typeone"] == "major" or mod["typetwo"] == "major": 
            majormc += int(mod["mc"])
        if mod["typeone"] == "majortwo" or mod["typetwo"] == "majortwo" or mod["typethree"] == "majortwo": 
            majortwomc += int(mod["mc"])
        if mod["typeone"] == "minorone" or mod["typetwo"] == "minorone" or mod["typethree"] == "minorone": 
            minoronemc += int(mod["mc"]) 
        if mod["typeone"] == "minortwo" or mod["typetwo"] == "minortwo" or mod["typethree"] == "minortwo": 
            minortwomc += int(mod["mc"]) 
        if mod["typeone"] == "minorthree" or mod["typetwo"] == "minorthree" or mod["typethree"] == "minorthree": 
            minorthreemc += int(mod["mc"])
            
    # for Y4S2
    for mod in yearfoursemtwoDB:
        totalmc += int(mod["mc"])
        if mod["grade"] == "S" or mod["grade"] == "U" or mod["grade"] == "NIL":
            sumc += int(mod["mc"])
        else:
            score += GradeScore(mod["grade"], int(mod["mc"]))
        if mod["ue"] == 1: 
            uemc += int(mod["mc"])   
        if mod["typeone"] == "uni": 
            unimc += int(mod["mc"]) 
        if mod["typeone"] == "fac": 
            facmc += int(mod["mc"])
        if mod["typetwo"] == "spec": 
            specmc += int(mod["mc"])
        if mod["typeone"] == "major" or mod["typetwo"] == "major": 
            majormc += int(mod["mc"])
        if mod["typeone"] == "majortwo" or mod["typetwo"] == "majortwo" or mod["typethree"] == "majortwo": 
            majortwomc += int(mod["mc"])
        if mod["typeone"] == "minorone" or mod["typetwo"] == "minorone" or mod["typethree"] == "minorone": 
            minoronemc += int(mod["mc"]) 
        if mod["typeone"] == "minortwo" or mod["typetwo"] == "minortwo" or mod["typethree"] == "minortwo": 
            minortwomc += int(mod["mc"]) 
        if mod["typeone"] == "minorthree" or mod["typetwo"] == "minorthree" or mod["typethree"] == "minorthree": 
            minorthreemc += int(mod["mc"])  
    
    # for Y4ST
    if len(yearfourSTDB) != 0:
        for mod in yearfourSTDB:
            totalmc += int(mod["mc"])
            if mod["grade"] == "S" or mod["grade"] == "U" or mod["grade"] == "NIL":
                sumc += int(mod["mc"])
            else:
                score += GradeScore(mod["grade"], int(mod["mc"]))
            if mod["ue"] == 1: 
                uemc += int(mod["mc"])   
            if mod["typeone"] == "uni": 
                unimc += int(mod["mc"]) 
            if mod["typeone"] == "fac": 
                facmc += int(mod["mc"])
            if mod["typetwo"] == "spec": 
                specmc += int(mod["mc"])
            if mod["typeone"] == "major" or mod["typetwo"] == "major": 
                majormc += int(mod["mc"])
            if mod["typeone"] == "majortwo" or mod["typetwo"] == "majortwo" or mod["typethree"] == "majortwo": 
                majortwomc += int(mod["mc"])
            if mod["typeone"] == "minorone" or mod["typetwo"] == "minorone" or mod["typethree"] == "minorone": 
                minoronemc += int(mod["mc"]) 
            if mod["typeone"] == "minortwo" or mod["typetwo"] == "minortwo" or mod["typethree"] == "minortwo": 
                minortwomc += int(mod["mc"]) 
            if mod["typeone"] == "minorthree" or mod["typetwo"] == "minorthree" or mod["typethree"] == "minorthree": 
                minorthreemc += int(mod["mc"]) 
                      
    try:      
        cap = round((score/(totalmc - sumc)),2)
    except ZeroDivisionError:
        cap = round(0.00,2)
        
    return render_template("plan.html",time=time, plan=plan, requirements=requirements, planID = planID, 
                           yOnesOnemod=yOnesOnemod, yearonesemone = yearonesemoneDB, yOnesTwomod=yOnesTwomod, 
                           yearonesemtwo = yearonesemtwoDB, yearoneST=yearoneSTDB, yOnesThreemod=yOnesThreemod, 
                           stOne=stOne , stTwo=stTwo, stThree=stThree, stFour=stFour, cap=cap , totalmc=totalmc, 
                           unimc=unimc, facmc=facmc, majormc=majormc, specmc=specmc, majortwomc=majortwomc, 
                           minoronemc=minoronemc, minortwomc=minortwomc, minorthreemc=minorthreemc, uemc=uemc, totalDmc=totalDmc, 
                           yTwosOnemod=yTwosOnemod, yeartwosemone = yeartwosemoneDB, yTwosTwomod=yTwosTwomod, 
                           yeartwosemtwo = yeartwosemtwoDB, yeartwoST=yeartwoSTDB, yTwosThreemod=yTwosThreemod,
                           yThreesOnemod=yThreesOnemod, yearthreesemone = yearthreesemoneDB, yThreesTwomod=yThreesTwomod, 
                           yearthreesemtwo = yearthreesemtwoDB, yearthreeST=yearthreeSTDB, yThreesThreemod=yThreesThreemod,
                           yFoursOnemod=yFoursOnemod, yearfoursemone = yearfoursemoneDB, yFoursTwomod=yFoursTwomod, 
                           yearfoursemtwo = yearfoursemtwoDB, yearfourST=yearfourSTDB, yFoursThreemod=yFoursThreemod)


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

@app.route("/settings")
def settings():

    time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return render_template("settings.html", time=time)

@app.route("/faq")
def faq():

    time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return render_template("faq.html", time=time)


@app.route("/about")
def about():

    time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return render_template("about.html", time=time)


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