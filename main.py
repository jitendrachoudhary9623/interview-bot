from flask import Flask, render_template, request, jsonify,make_response,session,logging,url_for,redirect,flash,abort
import aiml
import os
from nlp import TextAnalyser
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pdfkit
import json
from passlib.hash import sha256_crypt
from chartGenerators import generateChartsForPDF,getTimeStamp
from score import calculateScore
from db import *
from chatbot import Chatbot
from Auth import *
import threading

kernel = aiml.Kernel()
sid = SentimentIntensityAnalyzer()
def load_kern(forcereload):
	if os.path.isfile("bot_brain.brn") and not forcereload:
		kernel.bootstrap(brainFile= "bot_brain.brn")
	else:
		kernel.bootstrap(learnFiles = os.path.abspath("aiml/std-startup.xml"), commands = "load aiml b")
		kernel.saveBrain("bot_brain.brn")
load_kern(False)
#db=scoped_session(sessionmaker(bind=engine))
app = Flask(__name__)

totalQuestionToBeAsked=10


@app.route("/")
def index():
	return render_template("index.html")

@app.route("/home")
def home():
	if 'log' in session:
		for user in User.objects.filter(username=session["username"]):
			return render_template("home.html",user=user)
	abort(404)

@app.route("/register",methods=["GET","POST"])
def register():
	if 'log' in session:
		flash("Your already logged in your account, logout if you want to create new account","danger")
		return redirect(url_for("home"))
	else:
		if request.method == "POST":
			email=request.form.get("email")
			username=request.form.get("username")
			password=request.form.get("password")
			confirm=request.form.get("confirm")
			secure_password=sha256_crypt.encrypt(str(password))
			
			if password == confirm:

				user=User(username=username,password=secure_password,email=email)
				try:
					user.save()
				except:
					flash("Username or Email Id already exists ","danger")
					return redirect(url_for('register'))
				flash("Registeration successfull , Please Login ","success")
				return redirect(url_for('login'))
			else:
				flash("Password does not match","danger")
				return render_template('register.html')
		return render_template("register.html")

@app.route("/login",methods=["GET","POST"])
def login():
	if 'log' in session:
			flash("Already Logged in , To login with another account logout first","danger")
			return render_template('home.html')
	if request.method=="POST":
		username=request.form.get("username")
		password=request.form.get("password")
		for user in User.objects.filter(username=username).fields(username=1,password=1):
		
			if sha256_crypt.verify(password,user.password):
				session["log"]=True
				session["username"]=user.username
				flash("Welcome back {} ".format(user.username),"success")
				return redirect(url_for("home"))
			else:
				flash("Wrong password","danger")
				return render_template("login.html")
		flash("No user found please check your username","danger")
		return render_template("login.html")
	else:	
		return render_template("login.html")

@app.route("/logout")
def logout():
	if 'log' in session:
		session["log"]=False
		session.clear()
		flash("Logged out ,Thank you for using our service","success")
		return redirect(url_for("index"))
	else:
		flash("For logging out you need to login first","danger")
		return redirect(url_for("index"))

@app.route("/ppt")
def ppt():
	return render_template("ppt.html")
@app.route("/subscription",methods=["POST","GET"])
def subscription():
	availableInterview=getAvailableInterviews(session["username"])
	if request.method=="POST":
		no_of_interview=request.form.get("no")
		print(no_of_interview)
		addInterviews(session["username"],int(no_of_interview))
		flash("Interviews added","success")
		return redirect(url_for("subscription"))
	return render_template("subscription.html",available=availableInterview)
#route for main page
@app.route("/chatbot")
def chatbot():

	if 'log' in session:
		if getUserDetails(session["username"]).availableInterview<1:
			flash("Your interview Limit has been reached, get more from subscription page","danger")
			return redirect(url_for("home"))
		session["InterviewId"]=generateInterviewId()
		session["previousQuestion"]=""
		session["questionNo"]=0
		return render_template('beginInterview.html',username=session["username"],interviewid=session["InterviewId"]) #chatbot.html
	return render_template('notallowed.html')


@app.route("/interview",methods=["POST"])
def interview():
	if 'log' in session:
		beginInterview(session["username"],session["InterviewId"])
		updateAvailableInterview(session["username"])
		return render_template('interview.html',interviewId=session["InterviewId"])
	return render_template('notallowed.html')
	
@app.route("/interact",methods=["POST"])
def interact():

	answer=str(request.form['messageText'])
	emotion=json.loads(request.form['escore'])
	print(session["questionNo"])
	chatbot=Chatbot()
	response=chatbot.interact(username=session["username"],
				interviewId=session["InterviewId"],
				answer=answer,
				mode=0,
				emotion=emotion,
				previousQuestion=session["previousQuestion"])
	if session["questionNo"]==0:
		response["question"]="Introduce Yourself"
	
	if session["questionNo"]>totalQuestionToBeAsked:
		response["question"]="Thank you for giving the interview, you can click on finish interview for generating pdf"
	session["previousQuestion"]=response["question"]
	session["questionNo"]=session["questionNo"]+1
	response["questionNo"]=session["questionNo"]
	#print(response)
	return jsonify(response)


def savePdftoFile(name,data):
	directory="Report/{}".format(session["username"])
	if not os.path.exists(directory):
		os.makedirs(directory)
	f = open('{}/{}.pdf'.format(directory,name), 'w+b')
	binary_format = bytearray(data)
	f.write(binary_format)
	f.close()
	addReportPath(session["username"],'{}/{}.pdf'.format(directory,name))

@app.route('/generate',methods=['POST'])
def pdf_template():
	if 'log' in session:
		if request.method == 'POST' :
			message = str(request.form['data'])
			message=json.loads(message)
			echart,schart=generateChartsForPDF(message["emotion"],message["sentiment"],session["username"])
			#print(echart)
			rendered=render_template("pdf_template.html",transcript=message['transcript'],emotion=message["emotion"],totalDuration=message["interviewTime"],echart=echart,schart=schart)
			pdf=pdfkit.from_string(rendered,False)#true for client sending
			savePdftoFile("{}".format(session["InterviewId"]),pdf)
			#response=make_response(pdf)
			#response.headers['Content-Type']="application/pdf"
			#response.headers['Content-Disposition']="inline; filename=output.pdf" #change to attachment
			#return response
			return render_template("interviewComplete.html")
		
	abort(404)

@app.route("/viewReports")
def viewReports():
	if "log" in session:
		userdata=getAllInterviewsOfUser(session["username"])
		return render_template("viewAllReports.html",user=userdata)
	abort(404)
#error handlers
@app.errorhandler(404)
def error404(error):
	return render_template("notallowed.html"),404

@app.errorhandler(405)
def error405(error):
	return render_template("noaccess.html"),405
if __name__ == "__main__":

	app.secret_key="interviewbot"
	app.run(debug=True,port=12225,host="localhost",threaded=True)
