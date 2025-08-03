# /// script
# dependencies = ["pychallonge", "gspread"]
# ///

import json
import challonge 
import gspread
import helpers
import startgg

# Challonge setup
challonge_credentials = json.load(open("challonge_credentials.json"))
challonge.set_credentials(challonge_credentials["username"], challonge_credentials["private_key"])

# start.gg setup
startgg_credentials = json.load(open("startgg_credentials.json"))
startgg.set_access_token(startgg_credentials["access_token"])

# Google Sheets setup
sheet_details = json.load(open("sheet_details.json"))
sa = gspread.service_account(filename="credentials.json")
sh = sa.open(sheet_details["sheet_name"])

elo_ws = sh.worksheet(sheet_details["elo_worksheet"])
elo_list = elo_ws.get_all_records()

names_ws = sh.worksheet(sheet_details["player_names_worksheet"])
names_list = names_ws.get_all_records()

print("Preparing to update ELO ratings, there are currently", len(names_list),"players on the list")

(tournament_platform, tournament_name) = helpers.read_tournament_url()

# Create dictionnaries to access ELO by displayed player name
elo_dict = {}
names_dict = {}

for player in elo_list :
    elo_dict[player["Player Name"]] = player["ELO Score"]


if tournament_platform == "challonge.com" :
    for player in names_list :
        names_dict[player["Challonge_ID"]] = player["Player_Name"]

    tournament = challonge.tournaments.show(tournament_name)

    # Retrieve the participants
    participants = challonge.participants.index(tournament["id"])

    # Create a dictionnary to match challonge user id with tournament user id
    challonge_user_id_dict = {}

    for p in participants :
        challonge_user_id_dict[p["id"]] = p["challonge_user_id"]
        
    # Retrieve the matches    
    matches = challonge.matches.index(tournament["id"])

    # We will store the matches in a per-participant basis to facilitate ELO calculation
    # participant_matches[user_id] = [{"win_status", "opponent_id", "forfeited"}]
    participants_matches = {}
    for id in challonge_user_id_dict.values() :
        participants_matches[id] = []

    # Fill the per-participant matches
    for match in matches : 
        winner_dict = {}
        loser_dict = {}

        winner_id = challonge_user_id_dict[match["winner_id"]]
        loser_id = challonge_user_id_dict[match["loser_id"]]
        
        winner_dict["win_status"] = 1
        winner_dict["opponent_id"] = loser_id
        winner_dict["forfeited"] = match["forfeited"]
        
        loser_dict["win_status"] = 0
        loser_dict["opponent_id"] = winner_id
        loser_dict["forfeited"] = match["forfeited"]
        
        participants_matches[winner_id].append(winner_dict)
        participants_matches[loser_id].append(loser_dict)

elif tournament_platform == "www.start.gg" :
    for player in names_list :
        names_dict[player["StartGG_ID"]] = player["Player_Name"]
    players = startgg.get_players(tournament_name)
    sets = startgg.get_sets(tournament_name)

    participants_matches = {}
    for p in players :
        participants_matches[p["id"]] = []

    for set in sets :
        winner = max(set["players"], key=lambda p: p["score"])
        loser = min(set["players"], key=lambda p: p["score"])

        winner_dict = {
            "win_status": 1,
            "opponent_id": loser["id"],
            "forfeited": loser["score"] == -1
        }
        loser_dict = {
            "win_status": 0,
            "opponent_id": winner["id"],
            "forfeited": loser["score"] == -1
        }

        participants_matches[winner["id"]].append(winner_dict)
        participants_matches[loser["id"]].append(loser_dict)


# Compute the new ELO values and store them in a dict
new_elo_dict = {}
for participant in participants_matches :   
    if (len(participants_matches[participant]) != 0) :      
        player_name = names_dict.get(participant)
        sheet_elo = elo_dict.get(player_name)
        player_elo = sheet_details["elo_base_value"]
        if sheet_elo :
            player_elo = sheet_elo
        else : 
            print("Adding new user", participant, player_name, "with baseline ELO", sheet_details["elo_base_value"])
        new_elo = player_elo
        for match in participants_matches[participant] : 
            if (match["forfeited"]) != True : 
                win_status = match["win_status"]
                other_name = names_dict.get(match["opponent_id"])
                other_elo = sheet_details["elo_base_value"]
                other_sheet_elo = elo_dict.get(other_name)
                if other_sheet_elo : 
                    other_elo = other_sheet_elo
                new_elo += sheet_details["elo_k_factor"] * (win_status - 1/(1+pow(10, (other_elo-player_elo)/400)))
        new_elo = round(new_elo)
        new_elo_dict[player_name] = new_elo
        print(player_name, ": Old ELO", player_elo, "| new ELO", new_elo)

# Send the new values to the sheet        
for player in new_elo_dict :
    cell = elo_ws.find(player)
    if cell :
        elo_ws.update_cell(cell.row + sheet_details["elo_row_offset"], cell.col + sheet_details["elo_col_offset"], new_elo_dict[player])
    else : 
        elo_ws.append_rows(values=[[player] + ["" for i in range(sheet_details["elo_col_offset"]-1)] + [new_elo_dict[player]]])