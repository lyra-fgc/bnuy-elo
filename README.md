# bnuy-elo

Automate an ELO ranking system using Challonge tournaments and have it accessible on a Google Sheet such as : https://docs.google.com/spreadsheets/d/1FOrYUCtggNw1riKsfSd6XMOn0j4sSe4KLwKaqqYsysQ/edit#gid=391820267.
#
## Setup

This will require a Python 3 install with the Pychallonge module (https://github.com/ZEDGR/pychallonge) and a functioning Google Sheets API setup (https://developers.google.com/sheets/api/quickstart/python?hl=fr)
#

Create the google sheet on which your ELO ranking will be displayed. 

Create a Google Cloud project and enable the Google Drive and Google Sheets API on it. Then create a service account and, on your ELO sheet, allow access to the newly created service account.

You then create a Key for the newly created service account, save it as JSON and put the downloaded "credentials.json" file in this folder.

You now have to create two sheets on the google sheets.

The first sheet will be used for ELO calculation and display. Name three columns respectively "Player Name", "Character" and "ELO Score".

The second sheet will be used to correspond Challonge username to the displayed name on the sheet, since these can be considerably different. Name three columns respectively "Challonge_ID", "Challonge_Name" and "Player_Name".

# 
The only thing left is filling the details in the .json files here. 

In sheet_details.json, fill the sheet_name (displayed at the top left of the Google Sheets), the name of the worksheet used for ELO and the name of the worksheet used for player names. You can also change the base ELO value and the K-factor that represents the maximum gain/loss in a single match.

In challonge_credentials.json, fill in your Challonge username and your API key.
#
## Usage

Run the bnuy-names.py script. When prompted, enter the name or URL of the tournament. For example, for https://saltyeu.challonge.com/fr/BBCF37, you can either enter the URL or saltyeu-BBCF37.

This will update the names sheet with new participants from this tournament.

You can then run bnuy-elo.py. Similarly enter the name or URL of the tournament. This will update ELO on the ELO sheet using the tournament results, inserting any new participant with the baseline ELO (pre-calculation). You might want to make a copy of the ELO sheet before running this in case you want to rollback.

If you now want to change the displayed names of certain participants, you can change it on the ELO Sheet and enter the new displayed name in the "Player Name" column in the corresponding player's row in the Player Names sheet.