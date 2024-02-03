#!/usr/bin/env python
import json
import discord
import requests

g_users = {} #{"username" : "user_id"}
g_webhookUrl = ""
g_userAgent = ""

def loadConfig():
    '''
    Load the users and discord auth token from a config file
    '''
    global g_users
    global g_webhookUrl
    global g_userAgent
    
    config = {}
    with open("config.json") as f:
       config = json.load(f)

    g_users = config["users"]
    g_webhookUrl = config["webhookUrl"]
    g_userAgent = config["userAgent"]

def getTrophyByUserId( userId ):
    '''
    Use the trackmania io api to get user information and extract the 
    trophy data. 

    Uses "https://trackmania.io/api/player/{Player ID}"
    '''
    tm_io_header = {"User-Agent" : g_userAgent}
    apiUrl = "https://trackmania.io/api/player/{0}".format( userId )
    response = requests.get(apiUrl, headers=tm_io_header)

    if response.ok:
        return response.json()["trophies"]["points"]
    else:
        return 0

def getCurrentScores():
    '''
    Return a map of user_ids : trophyScore 
    '''
    currentScoreMap = {}
    for user in g_users.keys():
        points = getTrophyByUserId( g_users[user] )
        currentScoreMap[ g_users[user] ] = points

    return currentScoreMap

def getPreviousScores():
    '''
    Check to see if we have a previous score file and load it up. 
    '''
    previousScores = {}
   
    try:
        with open("scores.json", "r") as f:
            previousScores = json.load(f)
    except: 
        pass
    
    return previousScores

def saveCurrentScores( currentScores ):
    '''
    Write the current scores to a local file. 
    '''

    with open("scores.json", "w") as f:
        json.dump( currentScores, f )

    
def postTrophyScoreboard():
    '''
    Post to discord a scoreboard of trophy points along with the delta 
    from the last time this was run. 
    '''
    #Try to get the scores written the last time this was run. 
    previousScoreMap = getPreviousScores()
    #Fetch the current scores
    currentScoreMap = getCurrentScores()
    #Save the current scores
    saveCurrentScores( currentScoreMap )

    #Create a sorted list of players, scores and deltas
    scoreboardList = []
    for user in g_users.keys():
        user_id = g_users[user]
        #If we don't have this user's score don't include them
        if user_id not in currentScoreMap:
            continue

        #Calculate the delta from the previous score
        delta = 0 
        if user_id in previousScoreMap:
            delta = currentScoreMap[user_id] - previousScoreMap[user_id]
            
        scoreboardList.append((user, currentScoreMap[user_id], delta))
        
    #Sort the list by the scores
    leaderList = sorted( scoreboardList, key=lambda x: x[1], reverse = True )

    #Build up the message string
    message = ""
    place = 1
    for player in leaderList:
        if player[2] != 0:
            message += f"{place}. {player[0]} {player[1]} +{player[2]}\n"
        else:
            message += f"{place}. {player[0]} {player[1]}\n"
        place += 1

    #Post to discord, print for now.  
    webhook = discord.SyncWebhook.from_url( g_webhookUrl )
    webhook.send(message)

if __name__ == '__main__':
    '''
    This program is intended to be run on a schedule or as a cron job. 
    Every time it runs it will post a message to our discord. 
    '''
    loadConfig()
    postTrophyScoreboard() 

