import re

def read_tournament_url():
    prompt = "Enter tournament URL (e.g. 'https://challonge.com/single_elim' or 'https://www.start.gg/tournament/les-veaux-bordelais-2025')\n"
    tournament_url = input(prompt).strip()
    m = re.match(r"(?:https://)(www\.start\.gg|(?:([^.]+)\.)?challonge\.com)/(?:tournament/)?([\w\.-]+)/?\w*", tournament_url)
    if m:
        tournament_platform = m.group(1)
        tournament_name = m.group(3)
        tournament_subdomain = m.group(2)
        if tournament_subdomain is not None:
            tournament_name = f"{tournament_subdomain}-{tournament_name}"
    else:
        raise ValueError(f"Couldn't parse URL: '{tournament_url}'")
    
    return (tournament_platform, tournament_name)