import requests
from bs4 import BeautifulSoup
import statsapi
import datetime


def get_team_id_by_name(team_name):
    team_name_map = {
        "guardians": "Cleveland Guardians",
        "reds": "Cincinnati Reds",
        "red-sox": "Boston Red Sox",
        "rays": "Tampa Bay Rays",
        "pirates": "Pittsburgh Pirates",
        "marlins": "Miami Marlins",
        "braves": "Atlanta Braves",
        "mets": "New York Mets",
        "phillies": "Philadelphia Phillies",
        "nationals": "Washington Nationals",
        "cardinals": "St. Louis Cardinals",
        "cubs": "Chicago Cubs",
        "brewers": "Milwaukee Brewers",
        "rockies": "Colorado Rockies",
        "diamondbacks": "Arizona Diamondbacks",
        "padres": "San Diego Padres",
        "dodgers": "Los Angeles Dodgers",
        "giants": "San Francisco Giants",
        "angels": "Los Angeles Angels",
        "athletics": "Athletics",
        "mariners": "Seattle Mariners",
        "rangers": "Texas Rangers",
        "twins": "Minnesota Twins",
        "blue-jays": "Toronto Blue Jays",
        "white-sox": "Chicago White Sox",
        "tigers": "Detroit Tigers",
        "royals": "Kansas City Royals",
        "orioles": "Baltimore Orioles",
        "yankees": "New York Yankees",
        "astros": "Houston Astros"
    }
    normalized_name = team_name_map.get(team_name.lower(), team_name)
    all_teams = statsapi.get('teams', {'sportIds': 1})['teams']
    for team in all_teams:
        if team['name'] == normalized_name:
            return team['id']
    return None


def extract_teams_from_href(href):
    box_score_part = href.strip('/').split('/')[-1]
    if "-vs-" in box_score_part:
        teams_and_rest = box_score_part.split("-vs-")
        away_team_part = teams_and_rest[0]
        home_and_rest = teams_and_rest[1]
        home_team_parts = home_and_rest.split('-')
        home_team = []
        for part in home_team_parts:
            if part.isdigit() and len(part) >= 4:
                break
            home_team.append(part)
        
        home_team_name = '-'.join(home_team)
        away_team_name = away_team_part
        return away_team_name, home_team_name
    return None, None


def get_player_id(player_name, team_id):
    players = statsapi.lookup_player(player_name)
    for player in players:
        if player["currentTeam"].get("id") == team_id:
            return player.get("id")
    return None


def extract_lineup(game_container, side_class, team_id):
    lineup = []
    lineup_ul = game_container.select_one(f"ul.lineup__list.{side_class}")
    if not lineup_ul:
        return lineup
    player_lis = lineup_ul.select("li.lineup__player")
    for player_li in player_lis[:9]:
        player_link = player_li.select_one("a[href^='/baseball/player/']")
        if player_link:
            player_name = player_link.get("title", "").strip()
            player_id = get_player_id(player_name, team_id)
            lineup.append({"id": player_id, "name": player_name})
    return lineup


def extract_name_from_link(link):
    if link:
        name_with_dashes = link['href'].rsplit('/', 1)[-1]
        parts = name_with_dashes.split('-')
        if parts[-1].isdigit():
            parts = parts[:-1]
        pitcher_name = ' '.join(parts)
        return pitcher_name.strip()
    return None


def extract_pitchers(game_container, home_team_id, away_team_id):
    home_pitcher_link = game_container.select_one(
        ".lineup__list.is-home .lineup__player-highlight-name a[href^='/baseball/player/']")
    if home_pitcher_link:
        home_pitcher_name = extract_name_from_link(home_pitcher_link)
        home_pitcher_id = get_player_id(home_pitcher_name, home_team_id)
    else:
        home_pitcher_name = None
        home_pitcher_id = None

    away_pitcher_link = game_container.select_one(
        ".lineup__list.is-visit .lineup__player-highlight-name a[href^='/baseball/player/']")
    if away_pitcher_link:
        away_pitcher_name = extract_name_from_link(away_pitcher_link)
        away_pitcher_id = get_player_id(away_pitcher_name, away_team_id)
    else:
        away_pitcher_name = None
        away_pitcher_id = None

    return {
        "home_pitcher": {"id": home_pitcher_id, "name": home_pitcher_name},
        "away_pitcher": {"id": away_pitcher_id, "name": away_pitcher_name},
    }


def get_game_id(date: str, home_team_id: int, away_team_id: int):
    schedule = statsapi.schedule(date=date)
    for game in schedule:
        if game["away_id"] == away_team_id and game["home_id"] == home_team_id:
            return game["game_id"]
    return None


def scrape_lineups(url: str, date: str):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    all_games = [{"date": date}]
    game_containers = soup.select("div.lineup.is-mlb")
    for game_container in game_containers:
        boxscore_link = game_container.select_one("a[href*='/baseball/box-score/']")
        if not boxscore_link:
            continue

        href = boxscore_link['href']
        home_team, away_team = extract_teams_from_href(href)
        home_team_id = get_team_id_by_name(home_team)
        away_team_id = get_team_id_by_name(away_team)
        game_id = get_game_id(date, home_team_id, away_team_id)
        
        pitchers = extract_pitchers(game_container, home_team_id, away_team_id)
        home_pitcher_name = pitchers["home_pitcher"]["name"]
        home_pitcher_id = pitchers["home_pitcher"]["id"]
        away_pitcher_name = pitchers["away_pitcher"]["name"]
        away_pitcher_id = pitchers["away_pitcher"]["id"]

        home_lineup = extract_lineup(game_container, "is-home", home_team_id)
        away_lineup = extract_lineup(game_container, "is-visit", away_team_id)

        lineup_info = {
            "game_id": game_id,
            "home_team": {
                "name": home_team,
                "id": home_team_id,
                "starting_pitcher": home_pitcher_name,
                "starting_pitcher_id": home_pitcher_id,
                "lineup": home_lineup
            },
            "away_team": {
                "name": away_team,
                "id": away_team_id,
                "starting_pitcher": away_pitcher_name,
                "starting_pitcher_id": away_pitcher_id,
                "lineup": away_lineup
            }
        }
        all_games.append(lineup_info)
    return all_games


def get_date_str(tomorrow: bool) -> str:
    offset = 1 if tomorrow else 0
    date = datetime.date.today() + datetime.timedelta(days=offset)
    return date.isoformat()


def get_today_lineups():
    date_str = get_date_str(tomorrow=False)
    return scrape_lineups(
        "https://www.rotowire.com/baseball/daily-lineups.php", date_str)


def get_tomorrow_lineups():
    date_str = get_date_str(tomorrow=True)
    return scrape_lineups(
        "https://www.rotowire.com/baseball/daily-lineups.php?date=tomorrow", date_str)