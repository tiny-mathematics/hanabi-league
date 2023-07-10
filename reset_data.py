import json
import pandas as pd

class DataManager:
    def __init__(self):
        self.constants = self.fetch_constants()
        self.player_data = self.fetch_player_data()
        self.player_game_data = self.fetch_player_game_data()
        self.variant_data = self.fetch_variant_data()
        
    def fetch_constants(self):
        with open('data/constants.json', 'r') as file:
            constants = json.load(file)
        return constants

    def fetch_player_data(self):
        player_data = pd.read_csv('data/player_data.tsv')
        return player_data

    def fetch_player_game_data(self):
        player_game_data = pd.read_csv('data/player_game_data.tsv')
        return player_game_data

    def fetch_variant_data(self):
        variant_data = pd.read_csv('data/variant_data.tsv')
        return variant_data

    def reset_data(self):
        self.player_game_data = pd.DataFrame(columns=self.player_game_data.columns)
        self.player_game_data.to_csv('data/player_game_data.tsv', index=False, sep="\t")

        self.player_data['player_rating'] = 1400
        self.player_data['top_streak'] = 0
        self.player_data['current_streak'] = 0
        self.player_data['number_of_games'] = 0
        self.player_data['number_of_max_scores'] = 0
        self.player_data.to_csv('data/player_data.tsv', index=False, sep="\t")

        self.variant_data['variant_rating'] = self.variant_data['variant_name'].map(self.constants['variant_base_ratings'])
        self.variant_data['number_of_games_variant'] = 0
        self.variant_data['number_of_max_scores_variant'] = 0
        self.variant_data.to_csv('data/variant_data.tsv', index=False, sep="\t")

        self.constants['latest_game_id'] = self.constants['starting_game_id'] - 1
        self.constants['total_games_played'] = 0
        self.constants['latest_run'] = None
        with open('data/constants.json', 'w') as file:
            json.dump(self.constants, file)

def main():
    data_manager = DataManager()
    data_manager.reset_data()

if __name__ == "__main__":
    main()
