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
username = challonge_credentials["username"]
private_key = challonge_credentials["private_key"]
challonge.set_credentials(username, private_key)

# start.gg setup
startgg_credentials = json.load(open("startgg_credentials.json"))
startgg.set_access_token(startgg_credentials["access_token"])

# Google Sheets setup
sheet_details = json.load(open("sheet_details.json"))
sa = gspread.service_account(filename="credentials.json")
sh = sa.open(sheet_details["sheet_name"])
names_ws = sh.worksheet(sheet_details["player_names_worksheet"])

names_list = names_ws.get_all_records(numericise_ignore = [2,4,5])
print("Preparing to update player names, there are currently", len(names_list), "players on the list")

(tournament_platform, tournament_name) = helpers.read_tournament_url()

if tournament_platform == "challonge.com" :
    tournament = challonge.tournaments.show(tournament_name)
    participants = challonge.participants.index(tournament["id"])
    users = [{"id": p["challonge_user_id"], "name": p["username"]} for p in participants]
    existing_ids = {g["Challonge_ID"] for g in names_list}
    def check_similar(line, user_name) :
        return (line["StartGG_GamerTag"].casefold() == user_name.casefold() or
                line["Player_Name"].casefold() == user_name.casefold() )
    def get_sheet_values(user, existing_line = {}) :
        return [[user["id"], user["name"],
                 existing_line.get("StartGG_ID", ''), existing_line.get("StartGG_GamerTag", ''),
                 existing_line.get("Player_Name", user["name"])]]

elif tournament_platform == "www.start.gg" :
    players = startgg.get_players(tournament_name)
    users = [{"id": p["id"], "name": p["gamerTag"]} for p in players]
    existing_ids = {g["StartGG_ID"] for g in names_list}
    def check_similar(line, user_name) :
        return (line["Challonge_Name"].casefold() == user_name.casefold() or
                line["Player_Name"].casefold() == user_name.casefold())
    def get_sheet_values(user, existing_line = {}) :
        return [[existing_line.get("Challonge_ID", ''), existing_line.get("Challonge_Name", ''),
                 user["id"], user["name"],
                 existing_line.get("Player_Name", user["name"])]]

else :
    raise ValueError(f"Unsupported platform: {tournament_platform}")

print("Users that participated in this tournament were :")
print([u["name"] for u in users])

missing = [u for u in users if u["id"] not in existing_ids]
for user in missing :
    similar = [l for l in names_list if check_similar(l, user["name"])]
    if len(similar) == 1 :
        [to_update] = similar
        player_name = to_update["Player_Name"]
        row = names_ws.find(player_name).row
        values = get_sheet_values(user, to_update)
        print("Merging into existing user", values)
        names_ws.update(values, f"A{row}:E{row}")
    else :
        values = get_sheet_values(user)
        print("Adding new user", values)
        names_ws.append_rows(values=values)
        
print("Player names updated, there is now", len(names_ws.get_all_records()), "players on the list")