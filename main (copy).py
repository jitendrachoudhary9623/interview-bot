from flask import Flask, render_template, request, jsonify
import aiml
import os

app = Flask(__name__)
kernel = aiml.Kernel()

if os.path.isfile("bot_brain.brn"):
    kernel.bootstrap(brainFile = "bot_brain.brn")
else:
    #kernel.bootstrap(learnFiles="std-startup.xml", commands="load aiml b")
    kernel.learn("./aiml/cn-startup.xml")
    kernel.respond("load aiml cnask")
    kernel.saveBrain("bot_brain.brn")

@app.route("/")
def hello():
    return render_template('chat.html')

@app.route("/ask", methods=['POST'])
def ask():
	message = request.form['messageText'].encode('utf-8').strip()


	# kernel now ready for use
	while True:
	    if message == "quit":
	        exit()
	    elif message == "save":
	        kernel.saveBrain("bot_brain.brn")
	    else:
	        bot_response = kernel.respond(message)
	        # print bot_response
	        return jsonify({'status':'OK','answer':bot_response})

if __name__ == "__main__":
    app.run(host='localhost',port=5003, debug=True)
