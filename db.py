from mongoengine import *
from datetime import datetime
import random
import string
import csv

from QuestionDetail import QuestionDetail
connect('interviewbot', host='localhost', port=27017)

class InterviewEvaluation(EmbeddedDocument):
	#squestionCount=IntField()
	question = StringField()
	answer = StringField()
	time= FloatField()
	score=FloatField()
	sentiment=DictField()
	emotion=DictField()
	textAnalysis=DictField()
	
class Interview(Document):
	created = DateTimeField(default=datetime.utcnow())
	username = StringField(required=True)
	interviewId = StringField(required=True,unique=True)
	user_response = ListField(EmbeddedDocumentField(InterviewEvaluation))


class Questionset(Document):
	questionId=StringField()
	questionType=StringField()
	question=StringField()
	category=StringField()
	subcategory=StringField()
	keywords=ListField()
	evaluable=BooleanField()


		
def getQuestionDetails(question):
	#print("Inside Question Detail")
	for q in Questionset.objects(question=question):
		ques= QuestionDetail(q.questionId,q.questionType,q.question,q.category,q.subcategory,q.keywords,q.evaluable)
		return ques

	
def questionSet(qid,qtype,question,category,subcategory,keywords,evaluable):
	'''
	ADDS QUESTION TO MONGODB
	'''
	if evaluable:
		question=Questionset(questionId=qid,
		questionType=qtype,
		question=question,
		category=category,
		subcategory=subcategory,
		keywords=keywords,
		evaluable=evaluable)
	else:
		question=Questionset(questionId=qid,
		questionType=qtype,
		question=question,
		category=category,
		subcategory=subcategory,
		evaluable=evaluable)
	question.save()
	print("question saved")
		
def addQuestions():
	
	'''
	READS CSV AND SAVE TO DB
	
	'''
	filename=input("enter filename\n")
	typ=input("questiontype\n")
	evaluable=False
	if typ=="t":
		evaluable=True
	with open(filename) as csv_file:
		csv_reader = csv.reader(csv_file, delimiter='\t')
		line_count = 0
		for row in csv_reader:
			if line_count == 0 or line_count==1:
			    #print(row[0],row[1],row[2],row[3])
			    line_count += 1
			else:

				questionSet(
				qid=typ+str(line_count-1),
				qtype=row[1],
				question=row[0],
				category=row[2],
				subcategory=row[3],
				keywords=row[4:],
				evaluable=evaluable)
				line_count += 1
		print(f'Processed {line_count} lines.')
	
def beginInterview(username,interviewId):
	#user=Interview(username=username,interviewId=interviewId)
	#user.user_response=[InterviewEvaluation(question="",answer="start interview")]	
	#user.save()
	user = Interview.objects(interviewId=interviewId).modify(upsert=True, new=True, set__username=username)

def saveInterview(interviewId,question,answer,score,sentiment=None,emotion=None,textAnalysis=None):
	time=datetime.timestamp(datetime.now())
	Interview.objects(interviewId=interviewId).update_one(push__user_response=InterviewEvaluation(
	question=question,
	answer=answer,
	time=int(time),
	score=score,
	emotion=emotion,
	sentiment=sentiment,
	textAnalysis=textAnalysis
	))

def generateInterviewId():
	while True:
		interviewId= ''.join(random.choices(string.ascii_uppercase + string.digits, k=15))
		check=Interview.objects(interviewId=interviewId)
		if(len(check)==0):
			return interviewId

		
#addQuestions()
'''
print("Hello")
username=input("enter username\n")
id1=input("enter interviewId\n")

while True:
	print("1.Create Interview")
	print("2.Add Responses")
	resp=int(input("Enter your choice\n"))
	if resp==1:
		print("1")
		beginInterview(username,id1)
	elif resp==2:
		question=input("Enter Question\n")
		answer=input("Enter Answer\n")
		saveInterview(id1,question,answer,0.75)
		
'''
def checkIfQuestionAlreadyAsked(interviewId,question):
	#i = Interview.objects.filter(interviewId=interviewId).fields(username=1, user_response={'$elemMatch': {'question': "Tell me about an instance where you have failed and what you learned from it."}})
	
	#for i in Interview.objects.filter(user_response__match={'answer': "ASK QUESTION"}):
	for i in Interview.objects(interviewId=interviewId):
		for j in i.user_response:
			if j.question==question:
				return True

	return False	

#c=checkIfQuestionAlreadyAsked(interviewId="MGBFOX8253XVVA1",question="Give an example of a time you had to respond to an unhappy manager/ customer/ colleague/ professor/ friend.")
#print(c)