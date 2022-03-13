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

    def run(self):
        # setup vars
        player_info = []
        # load from json
        match_info = json.load(open('all_match_info.json'))

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
        for i, match in enumerate(self.summoner_object.match_history):
            # idk why the match.id gets formatted before reaching the bottom, setting it here
            current_match_id = match.id

            # limit match amount
            if i < self.match_amount:

                # look for match_id in json
                if current_match_id not in match_info:

                    # iterate through participants in the match
                    for participant in match.participants:
                        try:
                            player_info.append({
                                'name': participant.summoner.name,
                                'rank': format_rank(participant),
                                'winrate': calc_winrate(participant),
                            })
                        except ValueError:
                            player_info.append({
                                'name': participant.summoner.name,
                                'rank': 'UNRANKED',
                                'winrate': 0,
                            })

                    # add to match list
                    match_info[current_match_id] = player_info
                else:
                    print("Match found, skipping...")

        # write to json
        write_to_json(resources_path, 'all_match_info', match_info)

    def debug(self):
        pass

    def empty_json(self):
        empty = {}
        write_to_json(resources_path, 'all_match_info', empty)


if __name__ == "__main__":
    # noinspection SpellCheckingInspection
    match_jacana = TDTrackerV02("TURBO JACANA", 3)
    match_jacana.run()
