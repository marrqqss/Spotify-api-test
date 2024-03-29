#We need to log in to a spotify account, then get the code to then get the token to access the information to spotify

import requests # to make HTTP requests from python
import urllib.parse # to parse the url

import spotykeys

from datetime import datetime, timedelta # to get the current date and time
from flask import Flask, redirect, request, jsonify

app = Flask(__name__) # create an instance of the Flask class
app.secret_key = 'mysecretkey' # set the secret key to store the session data

CLIENT_ID = spotykeys.clientid #to not leak with gitignore
CLIENT_SECRET = spotykeys.clientsecret
REDIRECT_URI = 'http://localhost:5000/callback'

AUTH_URL = 'https://accounts.spotify.com/authorize' #to get the user's permission to access data
TOKEN_URL = 'https://accounts.spotify.com/api/token' #to get an access token
API_BASE_URL = 'https://api.spotify.com/v1' #to access the Spotify Web API

session = {} #to store the session data

#app.route redirects to the url directory
#if a function does not return anything, it will return a 404 error
#flask is about moving from one endpoint to another kinda
@app.route('/') # define the route for the root for flask. Ex. google.com/ is root
def index():
    return "Welcome to my Spotify App! <a href='/login'>Login with Spotify</a>" # Redirects to endpoint /login

@app.route('/login') # define the route for the login for flask
def login():
    scope = 'user-read-private user-read-email' # define the scope of the access

    params = {
        'client_id': CLIENT_ID, # pass the client id
        'response_type': 'code', # pass the response type
        'scope': scope, # pass the scope
        'redirect_uri': REDIRECT_URI ,# pass the redirect uri
        'show_dialog': True #force the user to approve the app again. For easier debugging
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}" # parse (builds) the url automatically to authenticate the user using the params. ? is used to separate the url from the parameters

    print('login good')

    return redirect(auth_url) # redirect to the auth_url from Flask

@app.route('/callback') # define the route for the callback for flask if there is a callback 
def callback():
    if 'error' in request.args: #check if there's an error in the request arguments
        return jsonify({"error": request.args['error']}) #returns a json archive with error
    
    if 'code' in request.args: #if theres no problem in the request we can send the information we got from the login to get the token
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code', #It's assumed that the function that will be used will search in the dictionary this keywords. That's why we define them
            'redirect_uri': REDIRECT_URI,
            'client_id' : CLIENT_ID, 
            'client_secret' : CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body) #we send the request to the url with the data we got from the login and store the response
        token_info = response.json() #json is an text format that is compatible with python dictionaries. this returns a dictionary. we store the dictionary in token_info

        session['access_token'] = token_info['access_token'] #we store the access token in the session
        session['refresh_token'] = token_info['refresh_token'] #we store the refresh token in the session
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in'] #we store the expiration time in the session

        print('callback good')

        return redirect('/playlists')

@app.route('/playlists') # define the route for the playlists for flask
def get_playlists():
    if 'access_token' not in session:
        return redirect('/login') #if there's no access token, we redirect to the login page
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token') #if the token is expired, we redirect to the refresh token page
    
    headers = {
        'Authorization': f"Bearer {session['access_token']}" #we pass the access token in the header. f is used to be able to add variables in the string
    }

    response = requests.get(API_BASE_URL + '/me/playlists', headers=headers) #we send the request to the url with the headers and store the response
    playlists = response.json() #we store the response in the playlists variable

    print('playlist good')

    return jsonify(playlists) #we return the playlists in a json format, we could convert it to an html format if we wanted to. We can use this json as a dictionary in python to use the information

@app.route('/refresh-token') # define the route for the refresh token for flask
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id' : CLIENT_ID,
            'client_secret' : CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()

        session['access_token'] = new_token_info['access_token'] #we store the new access token in the session
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in'] #we store the new expiration time in the session

        print('refresh-token good')

        return redirect('/playlists')
    
if __name__ == '__main__': # if the script is executed with the python interpreter, do the following
    app.run(host='0.0.0.0', debug=True) # run the app in the local server and debug mode to see the errors