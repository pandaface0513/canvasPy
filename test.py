# import libraries
import canvaslms.api as api
import json

import pymongo

import os, os.path
from whoosh import index
from whoosh.fields import *
from whoosh.qparser import QueryParser

# set up the schema for the document
schema = Schema(nid=TEXT(stored=True), content=TEXT(stored=True))

# create index dir if it does not exists
if not os.path.exists('indexdir'):
    os.mkdir('indexdir')

# initiate index
ix = index.create_in('indexdir', schema)

# set up tags
tags = ['blue pill', 'education', 'secondary school', 'academy', 'influence', 'university', 'skill', 'online education', 'learning', 'tactic', 'analysis']

# set up the mongoDB
client = pymongo.MongoClient('localhost', 27017)
db = client.test
discussion = db.discussion

def populateData():
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
    for topic in topics:
        # print('id: ', topic['id'])
        # print('title: ', topic['title'])
        results = apiObj.allPages('courses/15003/discussion_topics/' + str(topic['id']) + '/view')
        results = results[0]['view']
        
        # converts to json, in a format that mongoDB likes?
        j = json.loads(json.dumps(results))
        
        # then store it on mongoDB
        discussion.insert(j)

    # declare completion!
    print('done storing')

def clearData():
    discussion.drop()
    print('done dropping')

def readingData(UID):
    # then tries to get the data back
    for entry in discussion.find({"user_id": UID}):
        print(entry['message'])

    # declare completion!
    print('done reading')

def writingData(UID):
    # make a writer
    writer = ix.writer()
    # fill index with entries from DB
    for entry in discussion.find({"user_id": UID}):
        writer.update_document(nid=str(entry['id']),
                               content=entry["message"])
    # commit the document
    writer.commit()
    
def searchingData(UID):
    # write the data first
    writingData(UID)
    # search inside index for entries containing 
    with ix.searcher() as searcher:
        print(UID)
        for tag in tags:
            query = QueryParser('content', ix.schema).parse(tag)
            results = searcher.search(query, limit=
                                      None, terms=True)
            print(results[1:2])
            for hit in results:
                print(hit.matched_terms())
                # print(hit["content"])
    print('done searching')

