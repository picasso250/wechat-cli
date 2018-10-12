# coding=utf-8

import itchat
import threading
import sys, os
import copy
from itchat.content import *

if os.name == 'nt':
    enableCmdQR = 1
else:
    enableCmdQR = 2
    import readline # 强哥说，windows下面不需要

# 最近交谈
recent = set()
# UserName => NickName(RemarkName)
user_table = dict()
last_talk = None # 最后一个交谈的人

def get_name(info):
    if len(info['RemarkName']) == 0:
        return info['NickName']
    else:
        return info['RemarkName']

def get_cmd_args(s):
    args = s.split(' ')
    cmd = args[0]
    if len(args)>=1:
        args.pop(0)
    return cmd, [ a.strip() for a in args if len(a.strip()) > 0 ]

@itchat.msg_register([TEXT, MAP, CARD, NOTE, SHARING])
def text_reply(msg):
    global last_talk
    FromUserName = msg['FromUserName']
    last_talk = FromUserName
    recent.add(FromUserName)
    if FromUserName in user_table:
        name = user_table[FromUserName]
    else:
        u = itchat.search_friends(userName=FromUserName)
        user_table[u['UserName']] = get_name(u)
        name = get_name(u)
    print(name, '%s: %s' % (msg['Type'], msg['Text']))

class Search():
    def __init__(self):
        c = itchat.instanceList[-1]
        self.updateLock = c.storageClass.updateLock
        self.memberList = c.memberList
        self.chatroomList = c.chatroomList
    def search_friends_w(self, name):
        with self.updateLock:
            contact = []
            for m in self.memberList:
                if any([name in m.get(k) for k in ('RemarkName', 'NickName', 'Alias')]):
                    contact.append(m)
            return copy.deepcopy(contact)
    def search_chatrooms_w(self, name):
        with self.updateLock:
            matchList = []
            for m in self.chatroomList:
                if name in m['NickName']:
                    matchList.append(copy.deepcopy(m))
            return matchList
    def search_all(self, name):
        contact = []
        for c in list(name):
            contact += self.search_friends_w(c)
        for c in list(name):
            contact += self.search_chatrooms_w(c)
        d = {}
        for c in contact:
            d[c['UserName']] = c
        return d

itchat.auto_login(enableCmdQR=enableCmdQR, hotReload=True)

# 开启记录消息
def run_itchat():
    itchat.run()

# 用另一个线程收取消息
recv_thread = threading.Thread(target=run_itchat, args=())
recv_thread.start()

me = itchat.search_friends()
user_table[me['UserName']] = '@me'

talking_to = None
promot="$ "

print("Type 'help' to get help")

# cmd loop
while True:
    s = input(promot)
    s = s.strip()
    if s == "":
        continue
    cmd,args = get_cmd_args(s)

    if cmd=="help":
        print("Usage:")
        print("ls\tList recent users")
        print("s\tSearch User")
        print("t\tTalk to someone")
        print("r\tChange to reply last message")
        print("logout\tLogOut")
    elif cmd == "ls" : # list
        for u in recent:
            print(u,user_table[u])
    elif cmd == 's' : # search
        if len(args) > 0:
            k = args[0]

            s = Search()
            d = s.search_all(k)
            for k,r in d.items():
                print(r['UserName'], r['RemarkName'], r['NickName'], r['Alias'])
                user_table[r['UserName']] = get_name(r)
        else:
            print("Usage: s name")
    elif cmd == "t": # talk
        if len(args) > 0:

            if args[0] in user_table:
                talking_to = args[0]
            else:
                k = args[0]

                ul = itchat.search_chatrooms(name=k)
                if len(ul)>0:
                    u=ul[0]
                    talking_to = u['UserName']
                    user_table[talking_to] = get_name(u)

                ul = itchat.search_friends(name=k)
                if len(ul)==0:
                    pass
                else:
                    u = ul[0]
                    talking_to = u['UserName']
                    user_table[talking_to] = get_name(u)

            if talking_to != None:
                promot = "> "+user_table[talking_to]+" $ "
                recent.add(talking_to)
        else:
            print("Usage: t @id")
    elif cmd == "r": # reply
            if last_talk != None:
                talking_to = last_talk
                promot = "> "+user_table[talking_to]+" $ "
    elif cmd == "logout":
        itchat.logout()
        sys.exit()
    else:
        if talking_to != None:
            itchat.send(s, toUserName=talking_to)

recv_thread.join()
