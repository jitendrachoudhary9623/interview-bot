import os
category=input(" Enter Category")
current_directory=os.getcwd()
path="{}/aiml/{}".format(current_directory,category)
print(current_directory)

if not os.path.exists(path):
	os.makedirs(path)

pattern=input(" Enter Pattern").upper()
srai=input(" Enter SRAI").upper()
with open("{}/{}.aiml".format(path,pattern), "+w") as f:
	f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<aiml>\n\n<category>\n<pattern>\n{}\n</pattern>\n<template>\n<random>\n<li></li>\n</random>\n</template>\n</category>\n\n".format(srai))
	
	f.write("<category>\n<pattern>\n{}\n</pattern>\n<template>\n<srai>\n{}\n</srai>\n</template>\n</category>\n\n".format(pattern,srai))
	f.write("<category>\n<pattern>\n_ {}\n</pattern>\n<template>\n<srai>\n{}\n</srai>\n</template>\n</category>\n\n".format(pattern,srai))
	f.write("<category>\n<pattern>\n{} *\n</pattern>\n<template>\n<srai>\n{}\n</srai>\n</template>\n</category>\n\n".format(pattern,srai))
	f.write("<category>\n<pattern>\n_ {} *\n</pattern>\n<template>\n<srai>\n{}\n</srai>\n</template>\n</category>\n\n</aiml>".format(pattern,srai))

