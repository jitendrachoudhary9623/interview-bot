
pattern=input("Enter Pattern").upper()

srai=input("Enter SRAI").upper()
y=input("You you want to generate Random generator?")
if y=="y":
	print("<category>\n<pattern>\n{}\n</pattern>\n<template>\n<random>\n<li></li>\n</random>\n</template>\n</category>\n".format(srai))


print("<category>\n<pattern>\n_ {} *\n</pattern>\n<template>\n<srai>\n{}\n</srai>\n</template></category>\n".format(pattern,srai))
print("<category>\n<pattern>\n{} *\n</pattern>\n<template>\n<srai>\n{}\n</srai>\n</template></category>\n".format(pattern,srai))
print("<category>\n<pattern>\n_ {}\n</pattern>\n<template>\n<srai>\n{}\n</srai>\n</template></category>\n".format(pattern,srai))
print("<category>\n<pattern>\n{}\n</pattern>\n<template>\n<srai>\n{}\n</srai>\n</template></category>\n".format(pattern,srai))

