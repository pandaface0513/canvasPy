# import libraries
import canvaslms.api as api
import json

from random import randint

import pymongo

import os, os.path
from whoosh import index
from whoosh.fields import *
from whoosh.qparser import QueryParser
from whoosh import query

# set up the schema for the document
schema = Schema(nid=TEXT(stored=True), content=TEXT(stored=True))

# create index dir if it does not exists
if not os.path.exists('indexdir'):
    os.mkdir('indexdir')

# initiate index
ix = index.create_in('indexdir', schema)

# set up tags
keys = ['blue pill', 'education', 'secondary school', 'academy', 'influence', 'university', 'skill', 'online education', 'learning', 'tactic', 'analysis']

# set up topics
t = []

# set up the mongoDB
client = pymongo.MongoClient('localhost', 27017)
db = client.CanvasDiscussion
RAW_DATA = db.RAW_DATA
SORT_DATA = db.SORT_DATA

def newJSON():
    # Get the authorization token from a file (Or from any other source.
    #   We just need a string containing the authorization token.
    authToken = api.getAuthTokenFromFile('token.txt')

    # Create our API object, giving the name of the server running the
    #   instance of Canvas and the authorization token that we'll use to
    #   authenticate our requests.
    apiObj = api.CanvasAPI('canvas.sfu.ca', authToken)

    # Call the API and get the all the discussion topics.
    topics = apiObj.allPages('courses/15003/discussion_topics')
    
    # run a for loop to extract entries
    for x in range(0, len(topics)):
        # prepare a new JSON document
        jayson = {}
        # store the topic id first
        jayson['discussion_num'] = topics[x]['id']
        jayson['discussion_title'] = topics[x]['title']
        # then get the messages
        results = apiObj.allPages('courses/15003/discussion_topics/' + str(topics[x]['id']) + '/view')[0]['view']
        # store the message in json post
        j = json.loads(json.dumps(results))
        jayson['posts'] = j
        # remember the list of topic
        if topics[x]['id'] not in t:
            t.insert(len(t)+1, topics[x]['id'])
        # store the jayson to mongoDB
        RAW_DATA.save(jayson)
    print("done storing")


##def populateData():
##    # Get the authorization token from a file (Or from any other source.
##    #   We just need a string containing the authorization token.
##    authToken = api.getAuthTokenFromFile('token.txt')
##
##    # Create our API object, giving the name of the server running the
##    #   instance of Canvas and the authorization token that we'll use to
##    #   authenticate our requests.
##    apiObj = api.CanvasAPI('canvas.sfu.ca', authToken)
##
##    # Call the API and get the all the discussion topics.
##    topics = apiObj.allPages('courses/15003/discussion_topics')
##
##    # run a for loop to extract entries
##    for topic in topics:
##        print('id: ', topic['id'])
##        print('title: ', topic['title'])
##        results = apiObj.allPages('courses/15003/discussion_topics/' + str(topic['id']) + '/view')
##        results = results[0]['view']
##        
##        # converts to json, in a format that mongoDB likes?
##        j = json.loads(json.dumps(results))
##        
##        # then store it on mongoDB
##        if not j:
##            print("view is empty")
##        else:
##            discussion.insert(j)
##            discussion.rename(str(topic['id']))
##            if str(topic['id']) not in t:
##                   t.insert(len(t)+1, str(topic['id']))
##            print(t)
##
##    # declare completion!
##    print('done storing')

def clearData():
##    cols = db.collection_names()
##    for col in cols:
##        if col != "system.indexes":
##            db.drop_collection(col)
    db.drop_collection("RAW_DATA")
    db.drop_collection("SORT_DATA")
    t = []
    print('done dropping')

def refresh():
    clearData()
    newJSON()

def writingUsers(topic):
    # empty array of users
    users = []
    # fill array with user id
    for discussion in RAW_DATA.find({"discussion_num": topic}):
        for post in discussion['posts']:
            try:
               u = post["user_id"]
            except KeyError:
               u = "no user"
            if u not in users:
                if u != "no user":
                    users.insert(len(users)+1, u)
    return users
    
def writingData(UID, topic):
    # make a writer
    writer = ix.writer()
    # make an array
    msg = []
    # fill index with entries from DB
    for discussion in RAW_DATA.find({"discussion_num": topic}):
        for post in discussion['posts']:
            try:
                if post['user_id'] == UID:
                    i = str(post['id'])
                    m = post['message']
                    msg.insert(len(msg)+1, i)
                    writer.update_document(nid=i, content=m)
            except KeyError:
                print("")
    # commit the document
    writer.commit()
    return msg

def run():
    # refresh the RAW_DATA
    refresh()
    # looping through all the discussion
    # prepare a new json
    jayson = list()
    for x in range(0, len(t)):
        # jayson['discussion_id'] = t[x]
        # getting an array of users in that dicussion topic
        users = writingUsers(t[x])
        # make an empty wrapper for users
        # jayson['users'] = {}
        # then loop through messages from each user
        usrs = list()
        for y in range(0, len(users)):
            # store the user in the discussion
            # jayson['users'][str(y)] = {} # make an empty wrapper for user[y]
            # jayson['users'][str(y)]['user_id'] = users[y]
            # write the data first to the writer
            msg = writingData(users[y], t[x])
            # make an empty wrapper for messages
            # jayson['users'][str(y)]['messages'] = {}
            messages = list()
            for m in range(0, len(msg)):
                # emtpy wrapper for messages
                # jayson['users'][str(y)]['messages'][str(m)] = {}
                # store message_id
                # jayson['users'][str(y)]['messages'][str(m)]['message_id'] = msg[m]
                # store randomly genenrated quality_rating
                # jayson['users'][str(y)]['messages'][str(m)]['quality_rating'] = randint(0, 5)
                # empty wrapper for add keywords
                # jayson['users'][str(y)]['messages'][str(m)]['keywords'] = {}
                keywords = list()
                for k in keys:
                    with ix.searcher() as searcher:
                        qp = QueryParser("content", ix.schema)
                        user_q = qp.parse(k)
                        allow_q = query.Term("nid", msg[m])
                        results = searcher.search(user_q, filter=allow_q, terms=True)
                        s = results.matched_terms() #set
                        # check if not empty
                        if len(s):
                            keywords.append(k)
                message = {'message_id': msg[m], 'quality_rating': randint(0,5), 'keywords': keywords}
                messages.append(message)
            usr = {'user_id': users[y], 'messages': messages}
            usrs.append(usr)
        discussion = {'discussion_id': t[x], 'users': usrs}
        jayson.append(discussion)
    # store the jayson to mongoDB
    j = json.loads(json.dumps(jayson))
    SORT_DATA.insert(j)
    print('done running')

##def keywordSearch():
##    # search inside index for entries containing 
##    with ix.searcher() as searcher:
##        for z in range(0, len(tags)):
##            tag = tags[z]
##            query = QueryParser('content', ix.schema).parse(tag)
##            results = searcher.search(query, limit=None, terms=True)
##    print("")
    
run()
