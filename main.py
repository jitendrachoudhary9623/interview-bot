from flask import Flask, render_template, request, jsonify,make_response
import aiml
import os
from nlp import TextAnalyser
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pdfkit

kernel = aiml.Kernel()
sid = SentimentIntensityAnalyzer()
def load_kern(forcereload):
	if os.path.isfile("bot_brain.brn") and not forcereload:
		kernel.bootstrap(brainFile= "bot_brain.brn")
	else:
		kernel.bootstrap(learnFiles = os.path.abspath("aiml/std-startup.xml"), commands = "load aiml b")
		kernel.saveBrain("bot_brain.brn")


app = Flask(__name__)

#route for main page
@app.route("/")
def hello():
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
    app.run(debug=True,port=5011)
