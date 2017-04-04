## valaquenta

# Introduction

For this project, I used the League of Legends API


## Installation Instructions

There are a few steps that need to be taken to use the code:

1) Obtain a Riot Games API key.  Go to developer.riotgames.com and sign up for an account, or log in if you already have one.  Your development API key will be under the tab "My Development API Key on" on the left-hand card of the main page.  

2) Install MongoDB.  Go to https://www.mongodb.com/download, select either "Community Server" or "Enterprise Server", and select the version appropriate to your OS.  Follow the instructions for installation.

3) Install Python 2.7 if it is not already installed.  I used the Anaconda distribution, which had several packages pre-installed.  The packages I use are:

os
requests
json
time
collections
pprint
logging

pymongo

All of these except for pymongo should come with most Python distibutions.  For pymongo, run the command 

pip install pymongo

4) The files api.py and scraper.py contain class definitions for the service.  There are two example scripts that can be run: example.py and scrape.py