import os
import time
import matplotlib.pyplot as plt
import numpy as np

def generateChartsForPDF(emotions,sentiments,username):
    a=generateChartForEmotions(emotions,username)
    #generateChartForSentiment(sentiments)
    return a,generateChartForSentiment(sentiments,username)

def generateChartForEmotions(emotions,username):
    ts = time.time()
    echartname="{}_{}_emotion.png".format(username,ts)
    emotion_values=emotions.values()
    emotion_names=emotions.keys()
    
    my_circle=plt.Circle( (0,0), 0.7, color='white')
    plt.pie(emotion_values, labels=emotion_names, colors=["#ff5722","#827717","#6200ea","#c51162","#3f51b5","#004d40","#9e9e9e"])
    p=plt.gcf()
    p.gca().add_artist(my_circle)
    plt.savefig('{}/Plots/{}'.format(os.getcwd(),echartname))
    return '{}/Plots/{}'.format(os.getcwd(),echartname)

def generateChartForSentiment(sentiments,username):
    plt.clf()
    ts = time.time()
    schartname="{}_{}_sentiment.png".format(username,ts)
    sentiment_labels=list(sentiments.keys())[0:3]
    sentiment_values=list(sentiments.values())[0:3]
    sentiment_values[1]=-1*sentiment_values[1]
    n = np.arange(len(sentiment_labels))
    plt.barh(n, sentiment_values,color=["green","red","plum"])
    plt.yticks(n, sentiment_labels)
    plt.savefig('{}/Plots/{}'.format(os.getcwd(),schartname))
    return '{}/Plots/{}'.format(os.getcwd(),schartname)

def getTimeStamp():
    return time.time()