import json
import cassiopeia as cas
import config
from colorama import Fore, Style
import pygame
import sys, os
import pprint

resources_path = "./"

# pygame
pygame.init()
# vars
font = pygame.font.SysFont('arial', 11)
# window
win_pos = (-1500, 380)
win_height = 1000
win_width = 700
os.environ['SDL_VIDEO_WINDOW_POS'] = '%i,%i' % win_pos
screen = pygame.display.set_mode((win_width, win_height))
# boxes
match_height = 100
match_offset = 5


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
                except FileNotFoundError:
                    for name in self.summoner_names:
                        if name not in info:
                            info[name] = {}
                    write_to_json(resources_path, 'all_match_info', info)
                return info

            # setup vars
            # load from json if available, else return empty dict with player names
            match_info = load_vars_from_json()

            # summoner vars
            summoner_object = cas.Summoner(name=summoner_name, region=cas.data.Region("EUW"))
            summoner_history = cas.MatchHistory(continent=cas.data.Continent("EUROPE"),
                                                puuid=summoner_object.puuid,
                                                queue=cas.Queue.ranked_solo_fives, begin_index=0,
                                                end_index=self.match_amount + 1)

            # iterate through match history
            for i, match in enumerate(summoner_history):

                player_info = []

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

                # idk why the match.id gets formatted before reaching the bottom, setting it here
                current_match_id = match.id

                # limit matches
                if i == self.match_amount:
                    break
                # look for match_id in json
                if current_match_id in match_info[summoner_name]:
                    print(current_match_id + f" {Fore.GREEN}Match found,skipping...{Style.RESET_ALL}")
                else:
                    # iterate through participants in the match
                    for j, participant in enumerate(match.participants):
                        # vars
                        name = participant.summoner.name
                        rank = format_rank(participant)
                        winrate = calc_winrate(participant)
                        team = get_team_from_iter(j)
                        match_result = participant.stats.win

                        # set player stats
                        player_info.append({
                            'name': name,
                            'rank': rank,
                            'winrate': winrate,
                            'team': team,
                            'result': match_result
                        })

                    team_red = add_to_respective_team()[0]
                    team_blue = add_to_respective_team()[1]

                    team_red_wr = calc_team_winrate()[0]
                    team_blue_wr = calc_team_winrate()[1]

                    team_red_result = player_info[0]['result']
                    team_blue_result = player_info[5]['result']

                    # add to match
                    match_info[summoner_name][current_match_id] = {
                        'team_red': {
                            'avg_winrate': team_red_wr,
                            'result': team_red_result,
                            'players': team_red
                        },
                        'team_blue': {
                            'avg_winrate': team_blue_wr,
                            'result': team_blue_result,
                            'players': team_blue
                        }
                    }
            # write to json
            write_to_json(resources_path, 'all_match_info', match_info)


def start(c_player):
    scroll = 0
    all_match_info = json.load(open('all_match_info.json'))
    all_match_info = all_match_info[c_player]

    while True:
        # events
        for event in pygame.event.get():
            # quit event
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # mouse event
            mouse_pressed = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    scroll -= 1
                elif event.button == 3:
                    scroll += 1
        # draw BG
        bg_box = pygame.Rect(0, 0, win_width, win_height)
        pygame.draw.rect(screen, (0, 0, 0), bg_box)

        width = (win_width / 5) - 20
        height = (match_height / 2)

        for i, (match_key, match_value) in enumerate(all_match_info.items()):
            for m, (team_key, team_value) in enumerate(match_value.items()):
                avg_winrate = team_value['avg_winrate']
                player_list = team_value['players']

                for j, player in enumerate(player_list):

                    def set_winrate_color(wr):
                        # winrate color
                        wr_color = 'white'
                        # set based on winrate
                        if wr < 45:
                            wr_color = (249, 140, 182)
                        elif 45 <= wr <= 50:
                            wr_color = (252, 169, 133)
                        elif 50 < wr < 60:
                            wr_color = (133, 202, 93)
                        elif wr > 60:
                            wr_color = (100, 200, 150)

                        return wr_color

                    # set vars
                    name = player['name']
                    rank = player['rank']
                    winrate = player['winrate']
                    team = player['team']
                    # result = player['result']
                    winrate_color = set_winrate_color(winrate)
                    display_info = '{} {}'.format(name, winrate)

                    # draw name boxes
                    name_box = pygame.Rect(width * j,
                                           (((height * i) * 2) + (height * m)) + (match_offset * i) + (100 * scroll),
                                           width,
                                           height)
                    pygame.draw.rect(screen, winrate_color, name_box)
                    # text
                    text_name = font.render(display_info, True, (0, 0, 0))
                    box_center_name = text_name.get_rect(center=name_box.center)
                    screen.blit(text_name, box_center_name)

        pygame.display.update()


if __name__ == "__main__":
    # noinspection SpellCheckingInspection

    # setup players
    players_Backup = ['TURBO JACANA', 'TURBO Trusty', 'TURBO ALUCO']
    players = ['TURBO Trusty']
    matches = 3

    # setup object
    TD_Object = TDTrackerV02(players, matches)
    TD_Object.run()

    # start pygame
    start('TURBO Trusty')
