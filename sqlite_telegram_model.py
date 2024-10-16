from peewee import *

db = SqliteDatabase(None)

class BaseModel(Model):
    class Meta:
        database = db

class Chat(BaseModel):
    tgid = BigIntegerField(unique=True)
    name = TextField(null = True)
    title = TextField(null = True)
    location = TextField(null = True)
    category = TextField(null = True)
    usr_cnt = IntegerField(default = 0)
    msg_cnt = IntegerField(default = 0)
    link = TextField(null = True)
    group = IntegerField(null = True)
    channel = IntegerField(null = True)
    in_set = BooleanField(default = False)

class User(BaseModel):
    tgid = BigIntegerField(unique=True)
    name = TextField(null = True)
    first_name = TextField(null = True)
    last_name = TextField(null = True)
    about = TextField(null = True)
    access_hash = BigIntegerField(null = True)
    photo_path = TextField(null = True)
    phone = TextField(null = True)

class Message(BaseModel):
    chat = ForeignKeyField(Chat, backref='messages')
    uid = CharField(unique=True)
    msg_id = IntegerField()
    grouped_id = IntegerField(null=True)
    user_tgid = BigIntegerField(null=True)
    user = ForeignKeyField(User, backref='messages', null=True)
    date = DateTimeField(null=True)
    content = TextField(null=True)
    views = IntegerField(null=True)
    link = TextField(null=True)
    media_path = TextField(null=True)
    site_name = TextField(null=True)
    fwd_msg = ForeignKeyField('self', backref='forwards', null=True)
    fwd_author = TextField(null = True)
    rply_msg = ForeignKeyField('self', backref='replies', null=True)

class UserOnChat(BaseModel):
    user = ForeignKeyField(User, backref='chats')
    chat = ForeignKeyField(Chat, backref='users')
    uid = CharField(unique=True)
    admin = BooleanField(default=False)