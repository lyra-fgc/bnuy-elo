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

print("Preparing to update tournament seeding, there are currently", len(participants),"players entered in the tournament")

# Create a dictionnary to match challonge user id with tournament user id
# Create a dictionnary to match tournament user name with tournament user id
challonge_user_id_dict = {}
challonge_tournament_name_dict = {}

for p in participants :
    challonge_user_id_dict[p["id"]] = p["challonge_user_id"]
    challonge_tournament_name_dict[p["id"]] = p["name"]
    
# Create dictionnaries to access ELO by displayed player name
elo_dict = {}
names_dict = {}

for player in elo_list :
    elo_dict[player["Player Name"]] = player["ELO Score"]
for player in names_list :
    names_dict[player["Challonge_ID"]] = player["Player_Name"]
    
elo_user_list = []

for id in challonge_user_id_dict :
    challonge_id = challonge_user_id_dict[id]
    player_name = names_dict.get(challonge_id)
    sheet_elo = elo_dict.get(player_name)
    player_elo = sheet_details["unseeded_elo_value"]
    if sheet_elo :
        player_elo = sheet_elo
    elo_user_list.append({"id": id, 
                          "elo": player_elo, 
                          "ELO_name": player_name, 
                          "name": challonge_tournament_name_dict[id]})

def eloSort(entry) :
    return entry["elo"]
elo_user_list.sort(key=eloSort)

for i in range(0, len(elo_user_list)) :
    print("User", elo_user_list[i], "is being seeded", (len(elo_user_list) - i))
    challonge.participants.update(tournament["id"], elo_user_list[i]["id"], 
                                  name=elo_user_list[i]["name"], 
                                  seed=(len(elo_user_list) - i))