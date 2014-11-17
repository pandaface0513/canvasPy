import canvaslms.api as api
import json

import pymongo

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

def readingData():
    # then tries to get the data back
    for entry in discussion.find({"user_id": 100724}):
        print(entry['message'])

    # declare completion!
    print('done reading')



