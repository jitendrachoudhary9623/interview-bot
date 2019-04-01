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

engine=create_engine("mysql+pymysql://root:root@localhost/register") 
kernel = aiml.Kernel()
sid = SentimentIntensityAnalyzer()

def load_kern(forcereload):
	if os.path.isfile("bot_brain.brn") and not forcereload:
		kernel.bootstrap(brainFile= "bot_brain.brn")
	else:
		kernel.bootstrap(learnFiles = os.path.abspath("aiml/std-startup.xml"), commands = "load aiml b")
		kernel.saveBrain("bot_brain.brn")

db=scoped_session(sessionmaker(bind=engine))
app = Flask(__name__)




@app.route("/")
def index():
	return render_template("index.html")

@app.route("/home")
def home():
	if 'log' in session:
		return render_template("home.html")
	abort(404)

@app.route("/register",methods=["GET","POST"])
def register():
	if 'log' in session:
		flash("Your already logged in your account, logout if you want to create new account","danger")
		return redirect(url_for("home"))
	else:
		if request.method == "POST":
			name=request.form.get("name")
			username=request.form.get("username")
			password=request.form.get("password")
			confirm=request.form.get("confirm")
			secure_password=sha256_crypt.encrypt(str(password))
			
			if password == confirm:
				db.execute("INSERT INTO users(name,username,password) VALUES (:name,:username,:password)",{"name":name,"username":username,"password":secure_password})
				db.commit()
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
		uname=request.form.get("username")
		password=request.form.get("password")
		userdata=db.execute("SELECT username FROM users where username=:uname",{"uname":uname}).fetchone()
		passdata=db.execute("SELECT password FROM users where username=:uname",{"uname":uname}).fetchone()

		if userdata is None:
			flash("No user found please check your username","danger")
			return render_template("login.html")
		else:
			for pd in passdata:
				if sha256_crypt.verify(password,pd):
					session["log"]=True
					session["username"]=userdata[0]
					flash("Welcome back {} ".format(userdata[0]),"success")
					return redirect(url_for("home"))
				else:
					flash("Wrong password","danger")
					return render_template("login.html")
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
		load_kern(False)
		return render_template('chat.html') #chatbot.html
	return render_template('notallowed.html')

#route for chatbot
asked=[]
@app.route("/ask", methods=['POST','GET'])
def ask():
	print("Hello")
	message = str(request.form['messageText'])
	print(message)
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
	print(message)
	if message != "ask question" and message !="ASK QUESTION":
		scores = sid.polarity_scores(message)
		if scores['compound'] > 0:
			sentiment='Positive'
		elif scores['compound']< 0:
			sentiment='Negative'
		else:
			sentiment='Neutral'
		return jsonify({'status':'OK','sentiment_positive':scores['pos'],
	'sentiment_negative':scores['neg'],
	'sentiment_neutral':scores['neu'],
	'overall_sentiment':sentiment})	
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
			#print(message)
			message=d = json.loads(message)
			#message.username="OKsy"
			#print(message['transcript'])
			rendered=render_template("pdf_template.html",transcript=message['transcript'],emotion=message["emotion"],totalDuration=message["interviewTime"])
			pdf=pdfkit.from_string(rendered,False)#true for client sending
			response=make_response(pdf)
			response.headers['Content-Type']="application/pdf"
			response.headers['Content-Disposition']="inline; filename=output.pdf" #change to attachment
			return response
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
    app.run(debug=True,port=8242)
