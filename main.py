from flask import Flask, render_template, request, jsonify,make_response,session,logging,url_for,redirect,flash,abort
import aiml
import os
from nlp import TextAnalyser
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pdfkit
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session,sessionmaker
import json
from passlib.hash import sha256_crypt
from chartGenerators import generateChartsForPDF
from score import calculateScore
from db import *
from chatbot import Chatbot
from Auth import User
#engine=create_engine("mysql+pymysql://root:root@localhost/register") 
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

#route for main page
@app.route("/chatbot")
def chatbot():
	if 'log' in session:
		session["InterviewId"]=generateInterviewId()
		session["previousQuestion"]=""
		session["questionNo"]=0
		return render_template('beginInterview.html',username=session["username"],interviewid=session["InterviewId"]) #chatbot.html
	return render_template('notallowed.html')


@app.route("/interview",methods=["POST"])
def interview():
	if 'log' in session:
		beginInterview(session["username"],session["InterviewId"])

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

#route for chatbot
@app.route("/ask", methods=['POST','GET'])
def ask():
	#print("Hello")
	#print(str(request.form))
	message = str(request.form['messageText'])
	#print(request.form['escore'])
	#print(message)
	if message == "save":
			kernel.saveBrain("bot_brain.brn")
			return jsonify({"status":"ok", "answer":"Brain Saved"})
	elif message == "reload":
		load_kern(True)
		return jsonify({"status":"ok", "answer":"Brain Reloaded"})
	elif message == "quit":
		exit()
		return jsonify({"status":"ok", "answer":"exit Thank You"})
	else:
		bot_response = kernel.respond(message)
		if bot_response=="":
			bot_response=kernel.respond("NEXT QUESTION")
		return jsonify({'status':'OK','answer':bot_response})

#Route for sentiment analysis
@app.route('/sentiment',methods=['POST','GET'])
def sentiments():
	#print("sentiment")
	message = str(request.form['messageText'])
	emotion=json.loads(request.form['escore'])
	#print(message)
	if message != "ask question" and message !="ASK QUESTION":
		scores = sid.polarity_scores(message)
		if scores['compound'] > 0:
			sentiment='Positive'
		elif scores['compound']< 0:
			sentiment='Negative'
		else:
			sentiment='Neutral'
		
		sentiments={'sentiment_positive':scores['pos'],
		'sentiment_negative':scores['neg'],
		'sentiment_neutral':scores['neu']}
		#score=calculateScore(emotion,sentiments)
		return jsonify({'status':'OK','sentiment_positive':scores['pos'],
	'sentiment_negative':scores['neg'],
	'sentiment_neutral':scores['neu'],
	'overall_sentiment':sentiment,
	'score':0})	
	else:
		return jsonify({'status':'NOT PK'})		

#route for text analysis
@app.route('/textAnalysis',methods=['POST','GET'])
def text_analysis():
	userText = str(request.form['messageText'])
	#print(userText)
	
	if userText != "ask question" and userText !="ASK QUESTION":
		stemmingType = TextAnalyser.STEM
		language = "EN"
		myText = TextAnalyser(userText, language)
		myText.preprocessText(lowercase = userText,removeStopWords = userText,stemming = stemmingType)
		if myText.uniqueTokens() == 0:
				uniqueTokensText = 1
		else:
			uniqueTokensText = myText.uniqueTokens()
		#print('calls text analysis'+userText)
		#print(myText.getMostCommonWords(10))
		numChars=myText.length()
		numSentences=myText.getSentences()
		numTokens=myText.getTokens()
		top=myText.getMostCommonWords(10)
		lexical=myText.getTokens() / uniqueTokensText
		return jsonify({'status':200,'numChars': numChars,'numSentences':myText.getSentences(),'numTokens': myText.getTokens(),'uniqueTokens':uniqueTokensText,'topwords':top,'Lexical':lexical})
	else:
		return jsonify({'status':500,'numChars': 0,'numSentences':0,'numTokens': 0,'uniqueTokens':0,'topwords':0,'Lexical':0})


@app.route('/generate',methods=['POST'])
def pdf_template():
	if 'log' in session:
		if request.method == 'POST':
			message = str(request.form['data'])
			message=json.loads(message)
			echart,schart=generateChartsForPDF(message["emotion"],message["sentiment"],session["username"])
			print(echart)
			rendered=render_template("pdf_template.html",transcript=message['transcript'],emotion=message["emotion"],totalDuration=message["interviewTime"],echart=echart,schart=schart)
			pdf=pdfkit.from_string(rendered,False)#true for client sending
			response=make_response(pdf)
			response.headers['Content-Type']="application/pdf"
			response.headers['Content-Disposition']="inline; filename=output.pdf" #change to attachment
			return response
	abort(404)

@app.route("/trial")
def trial():
	return render_template("trial.html")

#error handlers
@app.errorhandler(404)
def error404(error):
	return render_template("notallowed.html"),404

@app.errorhandler(405)
def error405(error):
	return render_template("noaccess.html"),405
if __name__ == "__main__":
	app.secret_key="interviewbot"
	app.run(debug=True,port=12225,host="localhost")
