# coding=utf-8

import itchat, time
import threading
import readline
import sys, os
from itchat.content import *

# 最近交谈
recent = set()
# UserName => NickName(RemarkName)
user_table = dict()

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
    FromUserName = msg['FromUserName']
    recent.add(FromUserName)
    if FromUserName in user_table:
        name = user_table[FromUserName]
    else:
        u = itchat.search_friends(userName=FromUserName)
        user_table[u['UserName']] = get_name(u)
        name = u['RemarkName']
    print(name, '%s: %s' % (msg['Type'], msg['Text']))


if os.name == 'nt':
    enableCmdQR = 1
else:
    enableCmdQR = 2

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

print("Type help to get help")

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
        print("logout\tLogOut")
    elif cmd == "ls" : # list
        for u in recent:
            print(u,user_table[u])
    elif cmd == 's' : # search
        if len(args) > 0:
            k = args[0]
            ul = itchat.search_chatrooms(name=k)
            if len(ul)>0:
                u=ul[0]
                print("chat room found")
                UserName = u['UserName']
                user_table[UserName] = get_name(u)
                recent.add(UserName)
            ul = itchat.search_friends(name=k)
            u = None
            # search at every possible
            if len(ul) == 0:
                ul = itchat.search_friends(wechatAccount=k)
                if len(ul)==0:
                    print("no user")
                else:
                    u = ul[0]
            else:
                u = ul[0]
            if u != None:
                print (u)
                UserName = u['UserName']
                user_table[UserName] = get_name(u)
                recent.add(UserName)
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
    elif cmd == "logout":
        itchat.logout()
        sys.exit()
    else:
        if talking_to != None:
            itchat.send(s, toUserName=talking_to)

recv_thread.join()
