import tornado.ioloop
import os
import tornado.web
import tornado.websocket
import tornado.httpserver
from tornado.web import url
from couchbase.bucket import Bucket

WANTED_SUB_TYPES = ['NORMAL', 'RANKED_SOLO_5x5', 'RANKED_TEAM_5x5',
                    'CAP_5x5']


class MainHandler(tornado.web.RequestHandler):
    def check_origin(self, origin):
        return True

    def initialize(self):
        self.player_dict = bkt.get('Players').value
        self.champions = bkt.get('Champions').value

    def get(self):
        self.render("static/index.html", champions=self.champions['data'])


class PlayerHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True
   
    def initialize(self):
        self.player_dict = bkt.get('Players').value

    def on_message(self, message):
        player = message.lower()

        try:
            id = self.player_dict[player]['id']
        except KeyError:
            self.write_message('Summoner not found')
            return
        games = bkt.get('Matches::{}'.format(id)).value['games']
        kills = 0.0
        deaths = 0.0
        assists = 0.0
        for game in games:
	    if game['subType'] in WANTED_SUB_TYPES: 
            	try:
                    kills += game['stats']['championsKilled']
                except KeyError:
                    pass

                try:
                    deaths += game['stats']['numDeaths']
                except KeyError:
                    pass

                try:
                    assists += game['stats']['assists']
                except KeyError:
                   pass
        kills = kills / len(games)
        deaths = deaths / len(games)
        assists = assists / len(games)
        player = self.player_dict[player]['name']
        self.write_message('Stats for {}<br>Kills: {}<br>Deaths: {}<br>Assists: {}<br>Games: {}'.format(player, kills, deaths, assists, len(games)))


class ChampionHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True    

    def initialize(self):
        self.player_dict = bkt.get('Players').value
        self.champions = bkt.get('Champions').value

    def on_message(self, message):
        player, champion = message.split('::')
        player = player.lower()
        try:
            id = self.player_dict[player]['id']
        except KeyError:
            self.write_message('Summoner not found')

        games = bkt.get('Matches::{}'.format(id)).value['games']
        kills = 0.0
        deaths = 0.0
        assists = 0.0
        game_counter = 0.0
        for game in games:

            if game['subType'] in WANTED_SUB_TYPES and 
	            game['championId'] == self.champions['data'][champion]['id']:
                game_counter += 1
                try:
                    kills += game['stats']['championsKilled']
                except KeyError:
                    pass

                try:
                    deaths += game['stats']['numDeaths']
                except KeyError:
                    pass

                try:
                    assists += game['stats']['assists']
                except KeyError:
                    pass

        player = self.player_dict[player]['name']
        champion = self.champions['data'][champion]['name']

        if game_counter > 0:
            kills = kills / game_counter
            deaths = float(deaths) / game_counter
            assists = float(assists) / game_counter
            self.write_message('Stats for {}<br>Kills: {}<br>Deaths: {}<br>Assists: {}<br>Games: {}'.format(player, kills, deaths, assists, int(game_counter)))
        else:
            self.write_message('No games found for {} playing {}'.format(player, champion))

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
                url(r"/player", PlayerHandler),
                url(r"/champion", ChampionHandler),
                url(r"/", MainHandler),
            ]
        settings = {
                "debug": True,
                "static_path": os.path.join(os.path.dirname(__file__), "static")
            }
        tornado.web.Application.__init__(self, handlers, **settings)

if __name__ == "__main__":
    bkt = Bucket()
    server = tornado.httpserver.HTTPServer(Application())
    server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
