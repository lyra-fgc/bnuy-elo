import requests
import logging
import math

_access_token = None

def set_access_token(access_token):
    global _access_token
    _access_token = access_token

def send_request(operation_name, variables):
    global _access_token

    with open("startgg.graphql") as f:
        query = f.read()
    body = {"query": query, "operationName": operation_name, "variables": variables}
    resp = requests.post("https://api.start.gg/gql/alpha", headers={"Authorization": f"Bearer {_access_token}"}, json=body)
    content = resp.json()
    if "success" in content and not content["success"]:
        raise RuntimeError(content["message"])
    if "errors" in content:
        raise ExceptionGroup("GraphQL errors", [RuntimeError(e["message"]) for e in content["errors"]])
    return content["data"]

def get_bb_event(tournament_slug):
    data = send_request("GetTournament", {"slug": tournament_slug})
    if "tournament" not in data or data["tournament"] is None:
        raise RuntimeError(f"Tournament not found: '{tournament_slug}'")
    tournament = data["tournament"]
    if len(tournament["events"]) != 1:
        raise RuntimeError(f"[{tournament_slug}] Failed to find unique BBCF event.")
    event = tournament["events"][0]
    if event["entrants"]["pageInfo"]["totalPages"] > 1:
        raise RuntimeError(f"[{tournament_slug}] Somehow more than 500 entrants")
    logging.info(f"Using tournament '{tournament["name"]}', event '{event["name"]}', game '{event["videogame"]["name"]}'")
    return event

def get_players(tournament_slug):
    event = get_bb_event(tournament_slug)
    entrants = event["entrants"]["nodes"]
    return [p["player"] for e in entrants for p in e["participants"]]

def get_sets(tournament_slug):
    def player_id(entrant):
        [participant] = entrant["participants"] # Will raise if there's more than one participant. e.g. a team event.
        return participant["player"]["id"]
    per_page = 50

    event = get_bb_event(tournament_slug)
    player_ids = {e["id"]: player_id(e) for e in event["entrants"]["nodes"]}

    total_pages = math.ceil(event["sets"]["pageInfo"]["total"] / per_page)
    result = []
    for page in range(1, total_pages+1):
        data = send_request("GetSetPage", {"eventId": event["id"], "page": page, "perPage": per_page})
        for set in data["event"]["sets"]["nodes"]:
            result.append({
                "id": set["id"],
                "players": [{"id": player_ids[slot["entrant"]["id"]], "score": slot["standing"]["stats"]["score"]["value"]} for slot in set["slots"]]
            })

    return result