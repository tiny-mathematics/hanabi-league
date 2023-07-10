import json

import pandas as pd

def fetch_constants():
    with open('data/constants.json', 'r') as file:
        constants = json.load(file)
    return constants
    
def fetch_player_data():
    player_data = pd.read_csv('data/player_data.tsv')
    return player_data

def fetch_player_game_data():
    player_game_data = pd.read_csv('data/player_game_data.tsv')
    return player_game_data

def fetch_variant_data():
    variant_data = pd.read_csv('data/variant_data.tsv')
    return variant_data

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

def reset_data():
    global player_data, variant_data, player_game_data, constants

    player_game_data = pd.DataFrame(columns=player_game_data.columns)
    player_game_data.to_csv('data/player_game_data.tsv', index=False, sep="\t")

    player_data['player_rating'] = 1400
    player_data['top_streak'] = 0
    player_data['current_streak'] = 0
    player_data['number_of_games'] = 0
    player_data['number_of_max_scores'] = 0
    player_data.to_csv('data/player_data.tsv', index=False, sep="\t")

    variant_data['variant_rating'] = variant_data['variant_name'].map(variant_base_ratings)
    variant_data['number_of_games_variant'] = 0
    variant_data['number_of_max_scores_variant'] = 0
    variant_data.to_csv('data/variant_data.tsv', index=False, sep="\t")

    constants['latest_game_id'] = constants['starting_game_id'] - 1
    constants['total_games_played'] = 0
    constants['latest_run'] = None
    with open('data/constants.json', 'w') as file:
        json.dump(constants, file)


def main():
    constants = fetch_constants()
    player_data = fetch_player_data()
    player_game_data = fetch_player_game_data()
    variant_data = fetch_variant_data()

    reset_data()

if __name__ == "__main__":
    main()
