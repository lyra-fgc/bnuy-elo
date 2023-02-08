import json
import challonge 
import gspread

# Challonge setup
challonge_credentials = json.load(open("challonge_credentials.json"))
challonge.set_credentials(challonge_credentials["username"], challonge_credentials["private_key"])

# Google Sheets setup
sheet_details = json.load(open("sheet_details.json"))
sa = gspread.service_account(filename="credentials.json")
sh = sa.open(sheet_details["sheet_name"])

elo_ws = sh.worksheet(sheet_details["elo_worksheet"])
elo_list = elo_ws.get_all_records()

names_ws = sh.worksheet(sheet_details["player_names_worksheet"])
names_list = names_ws.get_all_records()

print("Preparing to update ELO ratings, there are currently", len(names_list),"players on the list")

# Create dictionnaries to access ELO by displayed player name
elo_dict = {}
names_dict = {}

for player in elo_list :
    elo_dict[player["Player Name"]] = player["ELO Score"]
for player in names_list :
    names_dict[player["Challonge_ID"]] = player["Player_Name"]

tournament_name = input("Enter tournament ID (e.g. 10230) or URL (e.g. 'single_elim' for challonge.com/single_elim).\nIf assigned to a subdomain, URL format must be :subdomain-:tournament_url (e.g. 'test-mytourney' for test.challonge.com/mytourney)\n")
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
# participant_matches[user_id] = [[win_status, other_user_id]]
participants_matches = {}
for id in challonge_user_id_dict :
    participants_matches[id] = []

# Fill the per-participant matches
for match in matches : 
    participants_matches[match["winner_id"]].append([1, match["loser_id"]])
    participants_matches[match["loser_id"]].append([0, match["winner_id"]])

new_elo_dict = {}

# Compute the new ELO values
for participant in participants_matches :
    challonge_id = challonge_user_id_dict[participant]
    player_name = names_dict.get(challonge_id)
    sheet_elo = elo_dict.get(player_name)
    player_elo = sheet_details["elo_base_value"]
    if sheet_elo :
        player_elo = sheet_elo
    else : 
        print("Adding new user", challonge_id, player_name, "with baseline ELO", sheet_details["elo_base_value"])
    new_elo = player_elo
    for match in participants_matches[participant] : 
        win_status = match[0]
        other_name = names_dict.get(challonge_user_id_dict[match[1]])
        other_elo = sheet_details["elo_base_value"]
        other_sheet_elo = elo_dict.get(other_name)
        if other_sheet_elo : 
            other_elo = other_sheet_elo
        new_elo += sheet_details["elo_k_factor"] * (win_status - 1/(1+pow(10, (other_elo-player_elo)/400)))
    new_elo = round(new_elo)
    new_elo_dict[player_name] = new_elo
    print(player_name, "old elo :", player_elo, "new_elo :", new_elo)

# Send the new values to the sheet        
for player in new_elo_dict :
    cell = elo_ws.find(player)
    if cell :
        elo_ws.update_cell(cell.row + sheet_details["elo_row_offset"], cell.col + sheet_details["elo_col_offset"], new_elo_dict[player])
    else : 
        elo_ws.append_rows(values=[[player] + ["" for i in range(sheet_details["elo_col_offset"]-1)] + [new_elo_dict[player]]])