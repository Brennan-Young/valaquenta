## valaquenta

1. [Introduction](README.md#introduction)
2. [Installation](README.md#installation)
3. [Design Considerations](README.md#design-considerations)
4. [Database Tables](README.md#database-tables)

## Introduction

This project was done as part of the interview process with a company (unnamed).  My task was to build a small service that scrapes data from an external API and stores it in a persistent store.

For this project, I decided to use the League of Legends API.  League of Legends is a competitive multiplayer game developed by Riot Games, with an estimated 100 million monthly active users.  I have attempted to make this project accessible to someone with no prior knowledge of League of Legends or Riot Games.  At a very high level, a match of League of Legends is like a match of chess, except with five players competing on each side.  Each player (called a "summoner") controls a single character ("champion") and works together with their teammates to destroy the opposing team's nexus.  

Riot Games provides an API which can be called to get information about League of Legends players and detailed information about the matches that are played  My project primarily builds a wrapper around the League of Legends API, which abstracts away some of the difficulties in using the API "as is".  Data retrieved from external API calls is stored in MongoDB, reducing the need for future calls to the API.  To aid in the understanding of this wrapper's functionality, I use it to develop a small sample program that computes some match statistics for a pair of professional League of Legends players.  I also spent a little bit of time working ona small piece that automatically scrapes data from the external API.

The reason that I chose the League of Legends API is threefold: firstly, I have been meaning to use the League of Legends API in a project for several months now, and this project looked like a good first step.  Secondly, I have a passion for eSports that made me very excited to get started on this project and build it out.  Lastly and arguably most importantly, matches in League of Legends produce interesting and rich data sets that offer tons of potential analysis.  Just as data science research has begun to make its way into real sports, I believe that data science will find a place in eSports, and I am excited to see how this develops over time.

## Installation

There are a few steps that need to be taken to use the code:

1) Obtain a Riot Games API key.  Go to developer.riotgames.com and sign up for an account, or log in if you already have one.  Your development API key will be under the tab "My Development API Key on" on the left-hand card of the main page.  With your API key, there are two approaches: the most straightforward way is to go to the files named "api.py" and "scraper.py", look for the class definitions "RiotAPI" and "Scraper", respectively, go to the functions named "__init__()", and in the field "self.api_key", replace "os.environ.get('RIOT_API_KEY')" with your API key.  Alternatively, export this key as an environment variable to ~/.profile (linux) or ~/.bash_profile (mac).

2) Install MongoDB.  Go to https://www.mongodb.com/download, select either "Community Server" or "Enterprise Server", and select the version appropriate to your OS.  Follow the instructions for installation (make sure to also start the MongoDB service).

3) Install Python 2.7 if it is not already installed.  I used the Anaconda distribution, which had several packages pre-installed.  The packages I use are:

os
requests
json
time
collections
pprint
logging

pymongo

All of these except for pymongo should come with most Python distibutions.  For pymongo, follow the instructions at http://api.mongodb.com/python/current/installation.html

4) The files api.py and scraper.py contain class definitions for the service.  There is an example script that can be run: example.py

# Riot API and My Work

The Riot API provides URLs to get data about League of Legends matches.  There are many different calls that can be made to the API, and I chose to implement wrappers for a subset of these possible calls for my project.  Namely, my API supports functionality to get the information of a player or players ("SUMMONER-V1.4"), get all the matches that a player has played ("MATCHLIST-V2.2"), and get the information of a particular match ("MATCH-V2.2").  Although the Riot API contains additional functionality, the implementation of these functions would not differ significantly from the ones currently implmented.  

The main work of this project is an end-user API, which serves as a wrapper to the Riot Games API.  This is envisioned as a class that another developer could use to produce useful applications.  

When a user uses the API to make a request, the API first checks the MongoDB database for the requested data.  If the data is there, it is returned, avoiding the need to make an API call to Riot Games.  If it is not, then an API call is made.  The data requested from the API is returned to the user and also stored in the database for future use.  

A fault of the above design is that not all data from the Riot API is static.  A player, for instance, can have their data change by leveling up in the League of Legends game or by playing additional matches.  Data stored in the database can thus become stale over time.  There were a few solutions to this problem considered: the two extremes are to never call the API unless the data is missing (produces stale data) and to always call it (expensive).  Ultimately, I decided to add a timestamp to all data containing the time at which the data was last received from the Riot API.  If this timestamp is older than some user-configurable time, then an API call is made to get fresh data.  

In a test setting, the Riot API limits the number of calls that can be made by a user in any given time window.  These are set to a limit of 10 calls per 10 seconds and 500 calls per 10 minutes.  In a production setting, these limits are increased, but in both cases this requires some techniques to handle the case where we have run out of tokens.  Some simple rate-limiting is implemented, allowing API calls to be made only when there are tokens available and logging situations where a call is attempted but no tokens are available.  There are cases where the application logic of functions does need to be changed to account for the possibility of not having enough tokens - consider cases where match info for all of the matches of a player is desired, requiring up to hundreds or thousands of nearly-simultaneous calls.  Handling such cases is a feature that I left to future work.  

## Design Considerations

This project uses two main technologies: the Python programming language to write the application and MongoDB to store the data.  Python here was used for two reasons: its high-level syntax makes it among the best languages for building out the first iteration of any system, and its readability and near-universality among engineers makes it easy to talk about and share.  MongoDB was chosen with a similar goal in mind - document-based stores work well in the early stages of a project when not all components of the data are not fully-understood.

I opted for a database instead of writing data directly to my file system to make the written data more accessible to later reads.  However, one possible next step would be to write all data into a distributed file system as well - this provides a later source of truth if and when the database goes down.

## Database Tables

MongoDB stores data into collections, which bear similarity to MySQL's tables (despite a wildly different schema).  In this project, three collection are used: playersCollection, playersMatches, and matches.

playersCollection is a list of different users, keyed by their username.  A call to the Riot API for the user "doublelift" would return the following json:

{"doublelift":{"id":20132258,"name":"Doublelift","profileIconId":1467,"revisionDate":1491204839000,"summonerLevel":30}}

Because I want to keep track of when this data was last put into the database, I add a field called "lastUpdated".  It would be possible to put this into the above json object directly, e.g. to make the above

{"doublelift":{"id":20132258,"name":"Doublelift","profileIconId":1467,"revisionDate":1491204839000,"summonerLevel":30, "lastUpdated": 1491283659.959528}}

However, I was hesitant to alter the json object received by the Riot API, so I decided instead on the following form:

{"doublelift": { "lastUpdated": 1491283659.959528 "info":{"id":20132258,"name":"Doublelift","profileIconId":1467,"revisionDate":1491204839000,"summonerLevel":30}}}

The choice to key by username is somewhat unintuitive, but stems from the fact that an end user of my API is more likely to be interested in looking up users by name rather than user ID, and this structure is more amenable to doing so.

playersMatches is a list of matches associated with a user, keyed again by username.