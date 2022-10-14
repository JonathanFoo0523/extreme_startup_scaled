from crypt import methods
from flask import Flask, render_template, request, redirect, make_response
from flaskr.player import Player
from flaskr.scoreboard import Scoreboard
import os
import threading
import requests
import time

app = Flask(__name__)

players = {}
# scoreboard = Scoreboard(os.getenv('LENIENT'))
scoreboard = {}
player_threads = {}


@app.route("/")
def index():
    return render_template("leaderboard.html", leaderboard=scoreboard)


@app.route("/players", methods=["GET", "POST"])
def add_player():
    if request.method == "GET":
        return render_template("add_player.html")
    else:
        player = Player(request.form["name"], request.form["url"])
        # scoreboard.new_player(player)
        scoreboard[player] = 0
        players[player.uuid] = player
        player_thread = threading.Thread(target=sendQuestion, args=(player,))
        player_threads[player.uuid] = player_thread
        player_thread.start()
        r = make_response(render_template("player_added.html", player_id=player.uuid))
        r.headers.set('UUID', player.uuid)
        return r 

@app.get("/players/<id>")
def player_page(id):
    player = players[id]
    return render_template("personal_page.html", name=player.name, id=player.uuid)


@app.get("/withdraw/<id>")
def remove_player(id):
    assert id in player_threads 
    thread = player_threads.pop(id) 
    del thread
    del scoreboard[players[id]]
    players[id].active = False
    del players[id]
    return redirect("/")


def sendQuestion(player):
    while player.active:
        r = requests.get(player.url, params={"q": "What is your name?"}).text
        if r == player.name:
            scoreboard[player] += 2
        else:
            scoreboard[player] -= 1
        time.sleep(1)
