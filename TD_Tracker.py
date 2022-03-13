import json
import cassiopeia as cas
import config

resources_path = "./"


def write_to_json(path, file_name, data):
    file_path = './' + path + '/' + file_name + '.json'
    with open(file_path, 'w') as fp:
        json.dump(data, fp, indent=1)


class TDTrackerV02:
    def __init__(self, summoner_name, match_amount):
        # make links
        self.summoner_name = summoner_name
        self.match_amount = match_amount
        # Cassiopeia setup
        cas.set_riot_api_key(config.api_key)
        # summoner vars
        self.summoner_object = cas.Summoner(name=self.summoner_name, region=cas.data.Region("EUW"))
        self.summoner_history = cas.MatchHistory(continent=cas.data.Continent("EUROPE"),
                                                 puuid=self.summoner_object.puuid,
                                                 queue=cas.Queue.ranked_solo_fives, begin_index=0, end_index=2)

    def run(self):
        # setup vars
        player_info = []
        # load from json
        match_info = {}
        try:
            match_info = json.load(open('all_match_info.json'))
            match_info = match_info[self.summoner_name]
        except KeyError:
            pass

        # helper methods
        def calc_winrate(part):
            wins = part.summoner.league_entries.fives.wins
            losses = part.summoner.league_entries.fives.losses
            winrate = round((wins / (wins + losses)) * 100, 2)
            return winrate

        def format_rank(part):
            rank = ''
            tier = part.summoner.league_entries.fives.tier.value
            division = part.summoner.league_entries.fives.division.value
            rank = "{} {}".format(tier, division)
            return rank

        # iterate through match history
        for i, match in enumerate(self.summoner_history):
            # idk why the match.id gets formatted before reaching the bottom, setting it here
            current_match_id = match.id

            # limit matches
            if i == self.match_amount:
                break

            # look for match_id in json
            if current_match_id in match_info:
                break

            # iterate through participants in the match
            for j, participant in enumerate(match.participants):

                # enforce limit, sometimes more than 10 participants are loaded
                if j > 10:
                    break

                # check in player has ranked stats
                try:

                    player_info.append({
                        'name': participant.summoner.name,
                        'rank': format_rank(participant),
                        'winrate': calc_winrate(participant),
                    })

                # add unranked if stats don't exist
                except:

                    player_info.append({
                        'name': participant.summoner.name,
                        'rank': 'UNRANKED',
                        'winrate': 0,
                    })

            # add to match list
            match_info[self.summoner_name] = {current_match_id: player_info}

        # write to json
        write_to_json(resources_path, 'all_match_info', match_info)

    def debug(self):
        pass

    def empty_json(self):
        empty = {}
        write_to_json(resources_path, 'all_match_info', empty)


if __name__ == "__main__":
    # noinspection SpellCheckingInspection
    # setup players
    matches = [TDTrackerV02("TURBO JACANA", 1), TDTrackerV02("TURBO Trusty", 1), TDTrackerV02("TURBO ALUCO", 1)]
    # run all players
    matches[0].empty_json()
    for player in matches:
        player.run()
