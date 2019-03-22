import aiml
import os

kernel = aiml.Kernel()

def load_kern(forcereload):
	if os.path.isfile("bot_brain.brn") and not forcereload:
		kernel.bootstrap(brainFile= "bot_brain.brn")
	else:
		kernel.bootstrap(learnFiles = os.path.abspath("aiml/std-startup.xml"), commands = "load aiml b")
		kernel.saveBrain("bot_brain.brn")

load_kern(True)

while True:	
	message=input("Enter Message : ")
	if message == "save":
	    	kernel.saveBrain("bot_brain.brn")
	elif message == "reload":
		load_kern(True)
	elif message == "quit":
		exit()
	else:		
		bot_response = kernel.respond(message)

	print(bot_response)
