import os
from bs4 import BeautifulSoup as Soup
import csv
questions=[]
os.chdir("aiml")
root=list(os.listdir())
path=os.getcwd()
newpath=path
def readFiles(directory,path):
	#print(directory)
	for d in directory:
		if len(d.split("."))==1:
			os.chdir(d)
			readFiles(list(os.listdir()),os.getcwd())
			os.chdir(path)
		else:
			typ=os.getcwd().split("/")[-1]
			text=""
			with open(d,'r',encoding = 'utf-8') as f:
				text+=f.read()
			soup = Soup(text)
			for e in soup.findAll('li'):
				element=str(e)
				element=element.split("<li>")[1]
				element=element.split("</li>")[0]
				if element=="":
					continue
				else:
					info=(d.split(".")[0],typ)
					questions.append((element,info))



print(path)
readFiles(root,newpath)
print(len(questions))
alreadyPresent=list()
with open('{}/q.csv'.format(os.getcwd()),'w') as f:
	for q in questions:
		info=q[1]
		if q[0] not in alreadyPresent:
			f.write("{},{},{}\n".format(q[0],info[0],info[1]))
			alreadyPresent.append(q[0])


