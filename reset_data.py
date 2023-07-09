import requests
import json

from dateutil.parser import parse

import pandas as pd
import numpy as np

from itertools import combinations

import datetime

def fetch_player_data():
    player_data = pd.read_csv('data/player_data.csv')
    return player_data

def fetch_constants():
    with open('data/constants.json', 'r') as file:
        constants = json.load(file)
    return constants

def fetch_player_game_data():
    player_game_data = pd.read_csv('data/player_game_data.csv')
    return player_game_data

def fetch_variant_data():
    variant_data = pd.read_csv('data/variant_data.csv')
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
