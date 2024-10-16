from telethon import errors
from peewee import *
from pathlib import Path
import os
from telethon.tl.types import Channel, MessageMediaPhoto, MessageMediaDocument, ChannelParticipantsAdmins, MessageMediaWebPage, PeerUser, WebPageEmpty, MessageReplyHeader, MessageFwdHeader, PeerChannel
from sqlite_telegram_model import db, BaseModel, Chat, User, Message, UserOnChat

class TelegramDump:
    def __init__(self, client, db_name):
        self.db_name = db_name
        self.client = client
        Path(self.db_name+"/media").mkdir(parents=True, exist_ok=True)
        
        db.init(self.db_name+"/"+self.db_name+".sqlite")
        #db.drop_tables([Chat, Message, User, UserOnChat])
        db.create_tables([Chat, Message, User, UserOnChat])

    def uid(self, cid, mid):
        return str(cid)+str(mid).zfill(10)

    def process_users(self, chat_tgid, chat_dbid, media=True):#todo: check if existed -> skip rest
        user_cnt = 0
        for user in self.client.iter_participants(chat_tgid):#todo: takeout
            user_cnt += 1
            #print(user)
            try:
                user_tgid = int(user.id)

                photo_path = None
                if (media is True) and (user.photo is not None):
                    #photo_path = self.client.download_profile_photo(user_tgid, self.db_name+"/media/"+"user-"+str(user_tgid))
                    #photo_path = os.path.basename(photo_path)
                    cnt = 0
                    for photo in self.client.iter_profile_photos(user):
                        fullfilename = self.client.download_media(photo)
                        filename, file_extension = os.path.splitext(fullfilename)
                        newfile = self.db_name+"/media/"+"user-"+str(user_tgid)+"-"+str(cnt)+"."+file_extension
                        os.replace(fullfilename, newfile)
                        if cnt == 0:
                            photo_path = newfile
                        cnt += 1
                
                user_dbid, created = User.get_or_create(
                    tgid = user_tgid,
                    defaults = {
                        'name': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        #'about': None,
                        'access_hash': int(user.access_hash), 
                        'photo_path': photo_path,
                        'phone': user.phone,
                    })
                if not created:
                    print("User already in set! updating...")
                    User.update(
                        name = user.username,
                        first_name = user.first_name,
                        last_name = user.last_name,
                        #about = None,
                        access_hash = int(user.access_hash), 
                        photo_path = photo_path,
                        phone = user.phone,
                    ).where(User.id == user_dbid).execute()


                UserOnChat.get_or_create(
                    uid = self.uid(chat_tgid, user_tgid),
                    defaults = {
                        'user': user_dbid,
                        'chat': chat_dbid,
                    })
            except Exception as e:
                print(e)

        #check for admin
        for user in self.client.iter_participants(chat_tgid, filter=ChannelParticipantsAdmins):#todo: takeout
            try:
                UserOnChat.update(admin = True).where(UserOnChat.uid == self.uid(chat_tgid, user.id)).execute()
            except Exception as e:
                print(e)
        return user_cnt

    def process_messages(self, chat_tgid, chat_dbid, media=True, start_date=None, end_date=None):
        message_cnt = 0
        try:
            with self.client.takeout(finalize=True) as takeout:
                if start_date:
                    print("start_date: "+str(start_date))
                    messages = takeout.iter_messages(chat_tgid, offset_date=start_date, reverse=True)
                elif end_date:
                    print("end_date: "+str(end_date))
                    messages = takeout.iter_messages(chat_tgid, offset_date=end_date, reverse=False)
                else:
                    messages = takeout.iter_messages(chat_tgid)
                for message in messages:#todo: takeout
                    message_cnt += 1
                    #print(message)
                    message_uid = self.uid(chat_tgid, message.id)
                    try:
                        #####REPLY######
                        rply_msg_id = None
                        if type(message.reply_to) is MessageReplyHeader:
                            rply_uid = self.uid(chat_tgid, message.reply_to.reply_to_msg_id)
                            #print("goc_rply")
                            rply_msg_id, created = Message.get_or_create(
                                uid = rply_uid,
                                defaults = {
                                    'chat': chat_dbid,
                                    'msg_id': message.reply_to.reply_to_msg_id,
                                })

                        #####FWD######
                        fwd_msg_id = None
                        fwd_author = None
                        if type(message.fwd_from) is MessageFwdHeader and type(message.fwd_from.from_id) is PeerChannel:
                            fwd_channel_id, created = Chat.get_or_create(
                                tgid = message.fwd_from.from_id.channel_id,
                                defaults = {
                                    'in_set': False,
                                })

                            fwd_uid = self.uid(message.fwd_from.from_id.channel_id, message.fwd_from.channel_post)
                            #print("goc_fwd")
                            fwd_msg_id, created = Message.get_or_create(
                                uid = fwd_uid,
                                defaults = {
                                    'chat': fwd_channel_id,
                                    'msg_id': message.fwd_from.channel_post,
                                    'date': message.fwd_from.date,
                                    'content': '' if message.message is None else message.message,
                                    'views': None if message.views is None else message.views,
                                })
                            fwd_author = message.fwd_from.post_author
                        msg_content = '' if message.message is None else message.message
                        msg_link = None
                        msg_site_name = None
                        #####MEDIA######
                        if message.media is not None and type(message.media) is MessageMediaWebPage and type(message.media.webpage) is not WebPageEmpty:
                            if msg_content != '':
                                msg_content += ' '
                            if message.media.webpage.title is not None:
                                msg_content += message.media.webpage.title
                                msg_content += ' '
                            if message.media.webpage.description is not None:
                                msg_content += message.media.webpage.description
                            msg_link = message.media.webpage.url
                            msg_site_name = message.media.webpage.site_name
                        
                        media_path = None
                        if media:
                            if type(message.media) is MessageMediaPhoto or (type(message.media) is MessageMediaDocument):# and 'video' not in message.media.document.mime_type):
                                media_path = self.client.download_media(message, self.db_name+"/media/"+message_uid)
                                media_path = os.path.basename(media_path)

                        user_tgid = None if type(message.from_id) is not PeerUser else message.from_id.user_id
                        user_dbid = None
                        if user_tgid is not None:
                            user_dbid, created = User.get_or_create(
                                tgid = user_tgid
                            )

                        message_dbid, created = Message.get_or_create(
                            uid = message_uid,
                            defaults = {
                                'chat': chat_dbid,
                                'msg_id': message.id,
                                'grouped_id': message.grouped_id,
                                'user_id':  user_tgid,
                                'user': user_dbid,
                                'date': message.date,
                                'content': msg_content,
                                'media_path': media_path,
                                'views': None if message.views is None else message.views,
                                'fwd_msg': fwd_msg_id,
                                'fwd_author': fwd_author,
                                'rply_msg': rply_msg_id,
                                'link': msg_link,
                                'site_name': msg_site_name,
                            })
                        if not created:
                            print(str(message_uid),str(message.id),str(message.date),str(message.views))
                            print("Message already in set! updating...")
                            Message.update(
                                chat = chat_dbid,
                                msg_id = message.id,
                                grouped_id = message.grouped_id,
                                user_id =  user_tgid,
                                user = user_dbid,
                                date = message.date,
                                content = msg_content,
                                media_path = media_path,
                                views = None if message.views is None else message.views,
                                fwd_msg = fwd_msg_id,
                                fwd_author = fwd_author,
                                rply_msg = rply_msg_id,
                                link = msg_link,
                                site_name = msg_site_name,
                            ).where(Message.id == message_dbid).execute()
                    except Exception as e:
                        print(e)
        except errors.TakeoutInitDelayError as e:
            print('Must wait', e.seconds, 'before takeout')
        except errors.UsernameNotOccupiedError as e:
            print("Groupname not found")

        return message_cnt

    def process_chat(self, chat_name, chat, location = "", category = "", media=True, start_date = None, end_date = None):
        if type(chat) is not Channel:#) and (type(chat) is not InputPeerChannel)
            return

        chat_tgid = chat.id#participants.chat_tgid
        is_group = chat.megagroup
        is_channel = chat.broadcast
        print(chat_tgid)
        #chat = client.get_entity(chat_tgid)
        #print(chat)
        chat_dbid = None
        try:
            chat_dbid, created = Chat.get_or_create(
                tgid = int(chat_tgid),
                defaults = {
                    'name': chat_name,
                    'title': chat.title,
                    'location': location,
                    'category': category,
                    'link': 'https://t.me/'+chat_name,
                    'group': int(is_group),
                    'channel': int(is_channel),
                    'in_set': True,
                })

            if not created:
                print("Chat already in set! updating...")
                Chat.update(
                    name = chat_name,
                    title = chat.title,
                    location = location,
                    category = category,
                    link = 'https://t.me/'+chat_name,
                    group = int(is_group),
                    channel = int(is_channel),
                    in_set = True,
                ).where(Chat.id == chat_dbid).execute()
        except Exception as e:
            print(e)

        usr_cnt = None
        if is_group:
            usr_cnt = self.process_users(chat_tgid, chat_dbid, media=media)
        else:
            usr_cnt = self.client.get_participants(chat_tgid, limit=0).total
        Chat.update(usr_cnt = usr_cnt).where(Chat.tgid == chat_tgid).execute()

        msg_cnt = self.process_messages(chat_tgid, chat_dbid, media=media, start_date=start_date, end_date = end_date)
        Chat.update(msg_cnt = msg_cnt).where(Chat.tgid == chat_tgid).execute()

        return chat_tgid