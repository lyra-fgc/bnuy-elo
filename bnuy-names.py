import json
import challonge 
import gspread

# Challonge setup
challonge_credentials = json.load(open("challonge_credentials.json"))
username = challonge_credentials["username"]
private_key = challonge_credentials["private_key"]
challonge.set_credentials(username, private_key)

# Google Sheets setup
sheet_details = json.load(open("sheet_details.json"))
sa = gspread.service_account(filename="credentials.json")
sh = sa.open(sheet_details["sheet_name"])
names_ws = sh.worksheet(sheet_details["player_names_worksheet"])

names_list = names_ws.get_all_records()
print("Preparing to update player names, there are currently", len(names_list), "players on the list")

tournament_name = input("Enter tournament ID (e.g. 10230) or URL (e.g. 'single_elim' for challonge.com/single_elim).\nIf assigned to a subdomain, URL format must be :subdomain-:tournament_url (e.g. 'test-mytourney' for test.challonge.com/mytourney)\n")
tournament = challonge.tournaments.show(tournament_name)
participants = challonge.participants.index(tournament["id"])

username_dict = {}

for p in participants :
    username_dict[p["challonge_user_id"]] = p["username"]

print("Users that participated in this tournament were :")
print(username_dict.values())

for user_id in username_dict : 
    tmp = [l for l in names_list if l["Challonge_ID"] == user_id]
    if len(tmp) == 0 :
        print("Adding new user", user_id, username_dict[user_id])
        names_ws.append_rows(values=[[user_id, username_dict[user_id], username_dict[user_id]]])
        
print("Player names updated, there is now", len(names_ws.get_all_records()), "players on the list")