from db import *
from passlib.hash import sha256_crypt

class User(Document):
    username=StringField(unique=True)
    password=StringField()
    email=StringField(unique=True)
    created = DateTimeField(default=datetime.utcnow())
