from flask import Flask, render_template, request, jsonify,make_response,session,logging,url_for,redirect,flash
import aiml
import os
from nlp import TextAnalyser
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pdfkit
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session,sessionmaker

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
	return render_template("home.html")

@app.route("/register",methods=["GET","POST"])
def register():
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
					flash("Welcome back {} ".format(userdata[0]),"success")
					return redirect(url_for("home"))
				else:
					flash("Wrong password","danger")
					return render_template("login.html")
	return render_template("login.html")

@app.route("/logout")
def logout():
	session["log"]=False
	session.clear()
	flash("Logged out ,Thank you for using our service","success")
	return redirect(url_for("login"))

#route for main page
@app.route("/chatbot")
def chatbot():
	load_kern(False)
	return render_template('chat.html')

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
		temp=bot_response
		if temp in asked:
			print("Already Asked")
			bot_response=kernel.respond("NEXT QUESTION")
			return jsonify({'status':'OK','answer':bot_response})
		asked.append(temp)
		print(bot_response)
		return jsonify({'status':'OK','answer':bot_response})

#Route for sentiment analysis
@app.route('/sentiment',methods=['POST','GET'])
def sentiments():
	print("sentiment")
	message = str(request.form['messageText'])
	print(message)
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

#route for text analysis
@app.route('/textAnalysis',methods=['POST','GET'])
def text_analysis():
	userText = str(request.form['messageText'])
	stemmingType = TextAnalyser.STEM
	language = "EN"
	myText = TextAnalyser(userText, language)
	myText.preprocessText(lowercase = userText,removeStopWords = userText,stemming = stemmingType)
	if myText.uniqueTokens() == 0:
       		uniqueTokensText = 1
	else:
		uniqueTokensText = myText.uniqueTokens()
	print('calls text analysis')
	print(myText.getMostCommonWords(10))
	numChars=myText.length()
	numSentences=myText.getSentences()
	numTokens=myText.getTokens()
	top=myText.getMostCommonWords(10)
	lexical=myText.getTokens() / uniqueTokensText
	return jsonify({'status':200,'numChars': numChars,'numSentences':myText.getSentences(),'numTokens': myText.getTokens(),'uniqueTokens':uniqueTokensText,'topwords':top,'Lexical':lexical})

@app.route('/generate',methods=['POST'])
def pdf_template():
	if request.method == 'POST':
		message = str(request.form['iTime'])
		print(message)
		rendered=render_template("pdf_template.html",totalDuration=str(request.form['iTime']))
		pdf=pdfkit.from_string(rendered,False)#true for client sending
		response=make_response(pdf)
		response.headers['Content-Type']="application/pdf"
		response.headers['Content-Disposition']="inline; filename=output.pdf" #change to attachment
		return response
if __name__ == "__main__":
    app.secret_key="interviewbot"
    app.run(debug=True,port=9138)
