import json
import cassiopeia as cas
import config
from colorama import Fore, Style

resources_path = "./"


def write_to_json(path, file_name, data):
    file_path = './' + path + '/' + file_name + '.json'
    with open(file_path, 'w') as fp:
        json.dump(data, fp, indent=1)


class TDTrackerV02:
    def __init__(self, summoner_names, match_amount):
        # make links
        self.summoner_names = summoner_names
        self.match_amount = match_amount
        # Cassiopeia setup
        cas.set_riot_api_key(config.api_key)

    def run(self):

        # iterate through all summoner names
        for summoner_name in self.summoner_names:

            def load_vars_from_json() -> dict:
                info = {}
                try:
                    info = json.load(open('all_match_info.json'))
                    # check if properly initialized
                    for name in self.summoner_names:
                        if name not in info:
                            info[name] = {}
                except json.decoder.JSONDecodeError:
                    # initialize empty dict
                    for name in self.summoner_names:
                        if name not in info:
                            info[name] = {}
                return info

            # setup vars
            player_info = []
            # load from json if available, else return empty dict with player names
            match_info = load_vars_from_json()

            # summoner vars
            summoner_object = cas.Summoner(name=summoner_name, region=cas.data.Region("EUW"))
            summoner_history = cas.MatchHistory(continent=cas.data.Continent("EUROPE"),
                                                puuid=summoner_object.puuid,
                                                queue=cas.Queue.ranked_solo_fives, begin_index=0,
                                                end_index=self.match_amount + 1)

            # helper methods
            def calc_winrate(part):
                try:
                    wins = part.summoner.league_entries.fives.wins
                    losses = part.summoner.league_entries.fives.losses
                    winrate = round((wins / (wins + losses)) * 100, 2)
                except ValueError:
                    winrate = 0
                return winrate

            def format_rank(part):
                try:
                    tier = part.summoner.league_entries.fives.tier.value
                    division = part.summoner.league_entries.fives.division.value
                    rank = "{} {}".format(tier, division)
                except ValueError:
                    rank = 'UNRANKED'
                return rank

            def get_team_from_iter(it):
                if it < 5:
                    team = 'red'
                else:
                    team = 'blue'
                return team

            def add_to_respective_team():
                # add player to respective team
                team_red = []
                team_blue = []
                for player in player_info:
                    if player['team'] == 'red':
                        team_red.append(player)
                    else:
                        team_blue.append(player)

                return team_red, team_blue

            def calc_team_winrate():
                # calc team winrate
                team_red_wr = 0
                team_blue_wr = 0
                # iterate through info to extract winrate
                for player in player_info:
                    if player['team'] == 'red':
                        team_red_wr += player['winrate']
                    else:
                        team_blue_wr += player['winrate']
                # cleanup
                team_red_wr = round(team_red_wr / 5, 2)
                team_blue_wr = round(team_blue_wr / 5, 2)

                return team_red_wr, team_blue_wr

            # iterate through match history
            for i, match in enumerate(summoner_history):
                # idk why the match.id gets formatted before reaching the bottom, setting it here
                current_match_id = match.id

                # limit matches
                if i == self.match_amount:
                    break

                # look for match_id in json
                if current_match_id in match_info[summoner_name]:
                    print(f"{Fore.GREEN}Match found,skipping...{Style.RESET_ALL}")
                    break

                # iterate through participants in the match
                for j, participant in enumerate(match.participants):
                    # vars
                    name = participant.summoner.name
                    rank = format_rank(participant)
                    winrate = calc_winrate(participant)
                    team = get_team_from_iter(j)
                    # set player stats
                    player_info.append({
                        'name': name,
                        'rank': rank,
                        'winrate': winrate,
                        'team': team
                    })

                team_red = add_to_respective_team()[0]
                team_blue = add_to_respective_team()[1]

                team_red_wr = calc_team_winrate()[0]
                team_blue_wr = calc_team_winrate()[1]

                # add to match
                match_info[summoner_name] = {current_match_id: {
                    'team_red': {
                        'avg_winrate': team_red_wr,
                        'players': team_red
                    },
                    'team_blue': {
                        'avg_winrate': team_blue_wr,
                        'players': team_blue
                    }
                }}
            # write to json
            write_to_json(resources_path, 'all_match_info', match_info)


if __name__ == "__main__":
    # noinspection SpellCheckingInspection

    # setup players
    players_Backup = ['TURBO JACANA', 'TURBO Trusty', 'TURBO ALUCO']
    players = ['TURBO JACANA']
    matches = 1

    # setup object
    TD_Object = TDTrackerV02(players, matches)
    TD_Object.run()
