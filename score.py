
import numpy as np

def minMaxScaler(array):
	minimum=min(array)
	maximum=max(array)
	scaled=[]
	for elem in array:
		scaled.append((elem-minimum)/(maximum-minimum))
	return np.asarray(scaled)
	
def emotionScore(emotion,evaluable=False):
	emo={"neutral":120,"sad":0,"fear":12,"disgust":0,"anger":10,"happy":70,"suprise":20}
	
	scalingFactor=0
	emotion_multiplier=np.asarray([1,-0.35,-0.35,-1.4,-1.4,1.4,-0.35])
	
	scaled=minMaxScaler(emotion.values())
	if evaluable:
		scalingFactor=0.25
	else:
		scalingFactor=0.40
	print("before 50%",sum(emotion_multiplier*scaled))
	score=sum(emotion_multiplier*scaled)*scalingFactor
	print("Emotion",score)
	return score/2
#print(emotionScore())

def sentimentScore(sentiment):
	#sentiment={"positive":0,"neutral":0.6,"negative":1}
	print(sentiment)
	sentiment_multilier=[3,1.9,0.9]
	s=np.asarray(list(sentiment.values()))*np.asarray(sentiment_multilier)
	print('after scale',s)
	score=(sum(s)/3)
	print("Sentiment",score)
	return score*0.40

def calculateScore(emotion,sentiment,lexical):
	print(emotion,type(emotion))
	e=emotionScore(emotion,evaluable=False)
	s=sentimentScore(sentiment)
	l=lexical*0.2
	print("lexical",l)
	#score=(s+e)/2
	score=s+e+l
	print("actual score ",score)
	if score > 0:
		return score
	return -score
