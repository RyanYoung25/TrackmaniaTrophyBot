#!/usr/bin/env python
import json
import discord
import logging
import requests
import time

g_users = {}
g_token = ""
g_userAgent = ""

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

g_nextRequestTime = None
g_previousScoreboardString = ""

def loadConfig():
    '''
    Load the users and discord auth token from a config file
    '''
    global g_users
    global g_token
    global g_userAgent
    
    config = {}
    with open("config.json") as f:
       config = json.load(f)

    g_users = config["users"]
    g_token = config["token"]
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

def getScoreboard():
    '''
    Return a scoreboard string that is sorted by trophy points
    '''

    trophyPointList = []

    #Get the trophy points for each user
    for user in g_users.keys():
        points = getTrophyByUserId( g_users[user] )
        trophyPointList.append((user, points))

    #Sort the trophy ordering
    leaderList = sorted( trophyPointList, key=lambda x: x[1], reverse = True )

    #Build the output string
    message = ""
    for place, player in enumerate(leaderList):
        message += f"{place + 1}. {player[0]} {player[1]}\n"

    return message

    

@client.event    
async def on_ready():
    '''
    Is called when the bot receives a discord event "ready"
    '''
    print(f'Logged on as {client.user}')

@client.event
async def on_message(message):
    '''
    Is called on *every* message sent. 
    '''
    global g_nextRequestTime
    global g_previousScoreboardString

    if message.author == client.user:
        #Got our own message, ignore it
        return

    if message.content.startswith('$scoreboard'):
        scoreboardString = g_previousScoreboardString
        if g_previousScoreboardString == "" or g_nextRequestTime is None or time.time() > g_nextRequestTime:
            #Make a request
            print("Making a request for trophy points")
            scoreboardString = getScoreboard()
            #Prevent discord spam from spaming the trackmania.io api
            g_previousScoreboardString = scoreboardString
            g_nextRequestTime = time.time() + 300

        await message.channel.send(scoreboardString)


if __name__ == '__main__':
    loadConfig()
    client.run(g_token)
