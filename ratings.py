import requests
import json

from dateutil.parser import parse

import pandas as pd
import numpy as np

from itertools import combinations

import datetime

def fetch_player_data():
    # Get data from Google Sheets
    # player_data_raw = gsheet.worksheet(player_data_sheet_name).get_all_values()

    # player_data = pd.DataFrame(player_data_raw[1:], columns=player_data_raw[0])

    # for column in ['top_streak', 'current_streak', 'number_of_games', 'number_of_max_scores']:
    #     player_data[column] = player_data[column].replace('', '0').astype(int)

    # for column in ['player_rating']:
    #     player_data[column] = player_data[column].replace('', str(player_base_rating)).astype(float)

    player_data = pd.read_csv('data/player_data.csv')

    return player_data

# Fetch metadata from Google Sheets
def fetch_constants():
    # Get data from Google Sheets
    # metadata_raw = gsheet.worksheet(metadata_sheet_name).get_all_values()

    # metadata = pd.DataFrame(metadata_raw[1:], columns=metadata_raw[0])

    # for column in ['latest_game_id', 'total_games_played']:
    #     metadata[column] = metadata[column].replace('', '0').astype(int)
    
    with open('data/constants.json', 'r') as file:
        constants = json.load(file)

    return constants

def fetch_player_game_data():
    # Get data from Google Sheets
    # player_game_data_raw = gsheet.worksheet(player_game_data_sheet_name).get_all_values()

    # player_game_data = pd.DataFrame(player_game_data_raw[1:], columns=player_game_data_raw[0])

    # for column in ['number_of_suits', 'number_of_players', 'score', 'max_score', 'player_game_number']:
    #     player_game_data[column] = player_game_data[column].replace('', '0').astype(int)

    # for column in ['player_rating', 'change_in_player_rating', 'avg_team_rating']:
    #     player_game_data[column] = player_game_data[column].replace('', str(player_base_rating)).astype(float)

    player_game_data = pd.read_csv('data/player_game_data.csv')

    return player_game_data

def fetch_variant_data():
    # Get data from Google Sheets
    # variant_data_raw = gsheet.worksheet(variant_data_sheet_name).get_all_values()

    # variant_data = pd.DataFrame(variant_data_raw[1:], columns=variant_data_raw[0])

    # variant_data['variant_rating'] = variant_data['variant_rating'].replace('', '0').astype(float)
    # variant_data['number_of_games_variant'] = variant_data['number_of_games_variant'].replace('', '0').astype(int)
    # variant_data['number_of_max_scores_variant'] = variant_data['number_of_max_scores_variant'].replace('', '0').astype(int)

    player_game_data = pd.read_csv('data/player_game_data.csv')

    return variant_data

# Define function for determining number of suits in a given variant
def get_number_of_suits(variant_name):
    # Special cases
    if variant_name == 'No Variant':
        return 5
    elif variant_name in ['Ambiguous & Dual-Color', 'Ambiguous Mix', 'Dual-Color Mix']:
        return 6

    # General case
    for num in range(3, 7):
        if f'{num} Suits' in variant_name:
            return num

    # If no number of suits was found
    raise ValueError(f'Cannot determine number of suits for variant "{variant_name}"')

# Define function for determining which suits are in a given variant
def find_variants(variant_name):
    suits = sorted(variant_data['variant_name'].unique(), key=len, reverse=True)

    variant_suits = []

    # Check for each suit if it is in the variant name
    for suit in suits:
        # If the suit is in the variant name, add it to the list and remove it from the variant name
        if suit in variant_name:
            variant_suits.append(suit)
            variant_name = variant_name.replace(suit, "")

    if not variant_suits:
        variant_suits.append('No Variant')

    return variant_suits

def build_variant_list():
    variants_raw = requests.get('https://hanab.live/api/v1/variants').json()

    # Variants with any of these words in the name will be excluded for the league
    filter_terms = [
        'ambiguous',
        'mix',
        'evens',
        'dark',
        'cocoa',
        'fives',
        'ones',
        'black',
        'gray',
        'matryoshka',
        'dual',
        'critical',
        'blind',
        'mute',
        'alternating',
        'duck',
        'cow',
        'synesthesia',
        'reversed',
        'down',
        'throw',
        'funnels',
        'chimneys'
    ]

    variants_raw = list(variants_raw.items())

    variants = pd.DataFrame(variants_raw, columns=['variant_id', 'variant_name'])
    variants['variant_id'] = variants['variant_id'].astype(int)
    variants = variants.drop('variant_id', axis=1)

    # Filter out the rows with specific terms in 'variant_name'
    pattern = '|'.join(filter_terms)
    variants = variants[~variants['variant_name'].str.lower().str.contains(pattern)]

    variants['number_of_suits'] = variants['variant_name'].apply(get_number_of_suits)
    variants = variants[variants['number_of_suits'].between(constants['min_suits'], constants['max_suits'])]
    variants['variants'] = variants['variant_name'].apply(find_variants)

    return variants

#  Fetch game data from hanab.live
def fetch_game_data():
    global player_data, variants
    # Fetch game data
    def fetch_data(player):
        url = f'https://hanab.live/api/v1/history-full/{player}?start={constants["starting_game_id"]}&end={constants["ending_game_id"]}'
        response = requests.get(url)
        return response.json()

    players = player_data['player_name'].unique()

    rows = []
    for player_name in players:
        data = fetch_data(player_name)

        for game in data:
            # Calculate game length in minutes
            start = parse(game["datetimeStarted"])
            end = parse(game["datetimeFinished"])
            length = (end - start).total_seconds() / 60

            if (
                not game["options"]["deckPlays"]
                and not game["options"]["emptyClues"]
                and not game["options"]["oneExtraCard"]
                and not game["options"]["oneLessCard"]
                and not game["options"]["allOrNothing"]
                and not game["options"]["detrimentalCharacters"]
            ):
                row = {
                    "game_id": game["id"],
                    "player_name": player_name,
                    "number_of_players": game["options"]["numPlayers"],
                    "datetime": start,
                    "game_length": length,
                    "score": game["score"],
                    "variant_id": game["options"]["variantID"],
                    "variant_name": game["options"]["variantName"],
                    "seed": game["seed"],
                    "number_of_turns": game["numTurns"],
                    "end_condition": game["endCondition"],
                    "player_names": game['playerNames']
                }
                rows.append(row)

    game_data = pd.DataFrame(rows)

    # Just new games
    game_data = game_data[game_data['game_id'] > constants['latest_game_id'].values[0]]
    game_data = game_data[game_data['game_id'] >= constants['starting_game_id']]
    game_data = game_data[game_data['game_id'] <= constants['ending_game_id']]

    if not game_data.empty:
        game_data = game_data[game_data['number_of_players'].between(constants['min_player_count'], constants['max_player_count'])]
        game_data = game_data[game_data['player_names'].apply(lambda x: set(x).issubset(players))]

        game_data = pd.merge(game_data, variants, on='variant_name')

        game_data = game_data.sort_values(by=['game_id', 'player_name'])

        return game_data

# Define functions for development coefficients
def calculate_development_coefficient(number_of_games, player_rating):
    if number_of_games <= 30:
        return 40
    elif player_rating <= 1600:
        return 30
    else:
        return 15

def calculate_league_development_coefficient(number_of_games_variant, variant_rating):
    if number_of_games_variant <= 30:
        return 20
    elif variant_rating <= 1600:
        return 10
    else:
        return 5


# Calculate player/variant ratings
def calculate_ratings():
    global variant_data, player_data, player_game_data, constants
    game_ids = game_data['game_id'].unique()
    game_ids.sort()

    print(len(game_ids), "games to parse")

    for i, game_id in enumerate(game_ids):
        noVar_rating = variant_data.loc[variant_data['variant_name'] == 'No Variant', 'variant_rating'].values[0]

        current_game = game_data.loc[game_data['game_id'] == game_id].copy()

        # Just storing this for score-hunting
        true_variant_name = current_game['variant_name'].values[0]

        # Calculate difficulty modifier
        difficulty_modifiers = [1]

        if current_game['number_of_players'].values[0] == 5:
            difficulty_modifiers[0] += constants['difficulty_modifier_5p']

        variant_names = current_game['variants'].values[0]
        variant_ratings = [variant_data.loc[variant_data['variant_name'] == name, 'variant_rating'].values[0] for name in variant_names]
        if len(current_game['variants'].values[0]) == 2:
            variant_rating_calculated = variant_ratings[0] + variant_ratings[1] - noVar_rating
            difficulty_modifiers += difficulty_modifiers
            difficulty_modifiers[0] += variant_rating_calculated / variant_ratings[0] - 1
            # just used for calculating the second variant's rating change
            difficulty_modifiers[1] += variant_rating_calculated / variant_ratings[1] - 1
        else:
            variant_rating_calculated = variant_data.loc[variant_data['variant_name'] == current_game['variants'].values[0][0], 'variant_rating'].values[0]

        player_names = current_game['player_names'].values[0]
        player_ratings = [player_data.loc[player_data['player_name'] == name, 'player_rating'].values[0] for name in player_names]
        avg_team_rating = sum(player_ratings) / len(player_ratings)

        current_game['variant_name'] = current_game['variants'].str[0]
        current_game = current_game.merge(player_data, on='player_name')
        current_game = current_game.merge(variant_data, on='variant_name')

        current_game['player_expected_results'] = (1-constants['u_v']) / (1 + 10 ** ((difficulty_modifiers[0] * variant_rating_calculated - current_game['player_rating']) / 400))

        team_expected_results = current_game['player_expected_results'].mean()

        max_score = 1 if current_game['score'].values[0] == current_game['number_of_suits'].values[0] * 5 else 0

        current_game['development_coefficient'] = current_game.apply(lambda row: calculate_development_coefficient(row['number_of_games'], row['player_rating']), axis=1)
        current_game['new_player_rating'] = current_game['player_rating'] + current_game['development_coefficient'] * (max_score - team_expected_results)

        # Note: More efficient way of doing the subsequent operations would be using .loc but making sure we are not operating on a view
        # This might result in SettingWithCopyWarning otherwise
        player_data = player_data.merge(current_game[['player_name', 'new_player_rating']], on='player_name', how='left')

        player_data['player_rating'] = np.where(player_data['new_player_rating'].isna(), player_data['player_rating'], player_data['new_player_rating'])
        player_data['number_of_games'] = np.where(player_data['new_player_rating'].isna(), player_data['number_of_games'], player_data['number_of_games'] + 1)
        player_data['number_of_max_scores'] = np.where(player_data['new_player_rating'].isna(), player_data['number_of_max_scores'], player_data['number_of_max_scores'] + max_score)
        player_data['current_streak'] = np.where(player_data['new_player_rating'].isna(), player_data['current_streak'], np.where(max_score == 0, 0, player_data['current_streak'] + 1))
        player_data['top_streak'] = np.where(player_data['new_player_rating'].isna(), player_data['top_streak'], np.maximum(player_data['current_streak'], player_data['top_streak']))

        player_data = player_data.drop(columns=['new_player_rating'])

        for i, variant_name in enumerate(variant_names):
            league_development_coefficient = calculate_league_development_coefficient(variant_data.loc[variant_data['variant_name'] == variant_names[i], 'number_of_games_variant'].values[0], variant_ratings[i])
            new_variant_rating = variant_ratings[i] + (league_development_coefficient / difficulty_modifiers[i]) * (team_expected_results - max_score)

            variant_data.loc[variant_data['variant_name'] == variant_names[i], 'variant_rating'] = new_variant_rating
            variant_data.loc[variant_data['variant_name'] == variant_names[i], 'number_of_games_variant'] += 1
            variant_data.loc[variant_data['variant_name'] == variant_names[i], 'number_of_max_scores_variant'] += max_score

        # Adding the required information to the DataFrame
        current_rating_info = current_game[['game_id', 'player_name', 'variant_name', 'number_of_suits', 'number_of_players', 'score', 'new_player_rating', 'player_rating']].copy()
        current_rating_info['variant_name'] = true_variant_name
        current_rating_info['max_score'] = max_score
        current_rating_info['avg_team_rating'] = avg_team_rating
        current_rating_info['change_in_player_rating'] = current_rating_info['new_player_rating'] - current_rating_info['player_rating']
        current_rating_info.drop(columns='player_rating', inplace=True)
        current_rating_info = current_rating_info.rename(columns={'new_player_rating': 'player_rating'})
        player_game_data = pd.concat([player_game_data, current_rating_info], ignore_index=True)
        constants['total_games_played'] += 1

    constants['latest_game_id'] = game_id
    constants['latest_run'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    player_game_data = player_game_data.sort_values(['player_name', 'game_id'])
    player_game_data['player_game_number'] = player_game_data.groupby('player_name').cumcount() + 1

    # necessary because google sheets is ridiculous
    player_game_data = player_game_data.reindex(columns=['game_id', 'player_name', 'player_game_number', 'variant_name', 'number_of_suits', 'number_of_players', 'score', 'max_score', 'player_rating', 'change_in_player_rating', 'avg_team_rating'])


# Update Google Sheets raw data
def update_google_sheets():
    # Update player data in Google Sheets
    gsheet.worksheet(player_data_sheet_name).clear()
    data_list = [player_data.columns.values.tolist()] + player_data.values.tolist()
    gsheet.worksheet(player_data_sheet_name).append_rows(data_list)

    # Update variant data in Google Sheets
    gsheet.worksheet(variant_data_sheet_name).clear()
    data_list = [variant_data.columns.values.tolist()] + variant_data.values.tolist()
    gsheet.worksheet(variant_data_sheet_name).append_rows(data_list)

    # Update player game data in Google Sheets
    gsheet.worksheet(player_game_data_sheet_name).clear()
    data_list = [player_game_data.columns.values.tolist()] + player_game_data.values.tolist()
    gsheet.worksheet(player_game_data_sheet_name).append_rows(data_list)

    # Update variant data in Google Sheets
    gsheet.worksheet(metadata_sheet_name).clear()
    data_list = [metadata.columns.values.tolist()] + metadata.values.tolist()
    gsheet.worksheet(metadata_sheet_name).append_rows(data_list)



def main():
    player_data = fetch_player_data()
    constants = fetch_constants()
    player_game_data = fetch_player_game_data()
    variant_data = fetch_variant_data()
    variants = build_variant_list()
    game_data = fetch_game_data()
    
    if game_data is not None and not game_data.empty:
        print("Calculating ratings")
        calculate_ratings()
        print("Updating Google Sheets")
        update_google_sheets()
        print("Done!")
    else:
        print('no new games')

if __name__ == "__main__":
    main()
