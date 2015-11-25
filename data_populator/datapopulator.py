from couchbase.bucket import Bucket
from couchbase.exceptions import NotFoundError
import riotwatcher
import time

player_list = ['Loltown', 'slugeraryer', 'So Damn Fancy',
               'Heratix', 'IZetris', 'hastore', 'The Tiltmeister', 'Noddres']

SLEEP_TIME = 15


class Populator():
    def __init__(self):
        self.watcher = riotwatcher.RiotWatcher(
            default_region=riotwatcher.EUROPE_WEST,
            key='4f973eb3-7400-4eaf-9e6b-05b9ca56068c')
        self.bkt = Bucket()
        self.player_dict = self.get_players()
        self.bkt.upsert('Champions', self.watcher.static_get_champion_list())
        while True:
            for _, v in self.player_dict.iteritems():
                self.update_recent_games(v)
                time.sleep(SLEEP_TIME)

    def get_players(self):
        try:
            player_dict = self.bkt.get('Players').value
        except NotFoundError:
            player_dict = self.watcher.get_summoners(names=player_list)
            self.bkt.upsert('Players', player_dict)
        return player_dict

    def update_recent_games(self, player):
        api_matches = self.watcher.get_recent_games(player['id'])
        cb_key = 'Matches::{}'.format(player['id'])
        try:
            db_matches = self.bkt.get(cb_key).value
        except NotFoundError:
            self.bkt.upsert(cb_key, api_matches)
        else:
            game_ids = list()
            for db_match in db_matches['games']:
                game_ids.append(db_match['gameId'])

            for api_match in api_matches['games']:
                if api_match['gameId'] in game_ids:
                    break
                else:
                    db_matches['games'].insert(0, api_match)

            self.bkt.upsert(cb_key, db_matches)

if __name__ == '__main__':
    Populator()
