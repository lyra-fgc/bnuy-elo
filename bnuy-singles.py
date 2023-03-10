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
    
matches = []

print("Enter match participants in winner-loser order using their displayed name on the ELO Sheet. Enter an empty line when you are done.")
while (match := input()) :
    matches.append({"winner" : match.split("-")[0], "loser" : match.split("-")[1]})
    
for match in matches :   
    winner_elo = elo_dict.get(match["winner"])
    loser_elo = elo_dict.get(match["loser"])

    new_winner_elo = winner_elo
    new_loser_elo = loser_elo
    
    new_winner_elo += sheet_details["elo_k_factor"] * (1 - 1/(1+pow(10, (winner_elo - loser_elo )/400)))
    new_loser_elo  += sheet_details["elo_k_factor"] * (0 - 1/(1+pow(10, (loser_elo  - winner_elo)/400)))

    new_winner_elo = round(new_winner_elo)
    new_loser_elo  = round(new_loser_elo)
    
    winner_cell = elo_ws.find(match["winner"])
    loser_cell  = elo_ws.find(match["loser"])
    
    elo_ws.update_cell(winner_cell.row + sheet_details["elo_row_offset"], winner_cell.col + sheet_details["elo_col_offset"], new_winner_elo)
    elo_ws.update_cell(loser_cell.row + sheet_details["elo_row_offset"], loser_cell.col + sheet_details["elo_col_offset"], new_loser_elo)

    print(match["winner"], ": Old ELO", winner_elo, "| new ELO", new_winner_elo)
    print(match["loser"], ": Old ELO", loser_elo, "| new ELO", new_loser_elo)
