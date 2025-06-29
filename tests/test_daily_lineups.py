import pytest
import daily_lineups
from unittest.mock import patch


@pytest.fixture
def mock_get_team_response():
    return {
        "teams": [
            {
                "id": 133,
                "name": "Athletics",
            }
        ],
    }


@pytest.fixture
def mock_lookup_player_same_name_response():
    return [
        {
            'id': 671277, 
            'fullName': 'Luis García Jr.', 
            'firstName': 'Luis', 
            'lastName': 'García', 
            'primaryNumber': '2', 
            'currentTeam': {'id': 120}, 
            'primaryPosition': {
                'code': '4', 
                'abbreviation': '2B'
            }, 
            'useName': 'Luis', 
            'boxscoreName': 'García Jr., L', 
            'mlbDebutDate': '2020-08-14', 
            'nameFirstLast': 'Luis García Jr.', 
            'nameSlug': 'luis-garcia-jr-671277',
            'firstLastName': 'Luis García Jr.', 
            'lastFirstName': 'García Jr., Luis', 
            'lastInitName': 'García Jr., L', 
            'initLastName': 'L García Jr.', 
            'fullFMLName': 'Luis Victoriano García Jr.', 
            'fullLFMName': 'García Jr., Luis Victoriano'
        }, 
        {
            'id': 472610, 
            'fullName': 'Luis García', 
            'firstName': 'Luis', 
            'lastName': 'García', 
            'primaryNumber': '57', 
            'currentTeam': {'id': 119}, 
            'primaryPosition': {
                'code': '1', 
                'abbreviation': 'P'
            }, 
            'useName': 'Luis', 
            'boxscoreName': 'García, L', 
            'nickName': 'Amadito', 
            'mlbDebutDate': '2013-07-10', 
            'nameFirstLast': 'Luis García', 
            'nameSlug': 'luis-garcia-472610', 
            'firstLastName': 'Luis García', 
            'lastFirstName': 'García, Luis', 
            'lastInitName': 'García, L', 
            'initLastName': 'L García', 
            'fullFMLName': 'Luis Amado García', 
            'fullLFMName': 'García, Luis Amado'
        }
    ]


@pytest.fixture
def mock_schedule_response():
    return [
        {
            "game_id": 777544,
            "game_datetime": "2025-06-12T17:10:00Z",
            "game_date": "2025-06-12",
            "game_type": "R",
            "status": "Final",
            "away_name": "Washington Nationals",
            "home_name": "New York Mets",
            "away_id": 120,
            "home_id": 121,
        }
    ]


@pytest.fixture
def mock_game_container():
    html = """
        <div class="lineup__box">
            <div class="lineup__main">
                <ul class="lineup__list is-home">
                    <li class="lineup__player-highlight mb-0">
                        <div class="lineup__player-highlight-name">
                            <a href="/baseball/player/home-pitcher-12345">Home Pitcher</a>
                            <span class="lineup__throws">R</span>
                        </div>
                        <div class="lineup__player-highlight-stats">
                            5-3&nbsp;3.50 ERA             
                        </div>

                        <li class="lineup__player">
                            <div class="lineup__pos">RF</div>
                            <a title="Player One" href="/baseball/player/player-one-11111">Player One</a>
                            <span class="lineup__bats">L</span>
                        </li>
                        <li class="lineup__player">
                            <div class="lineup__pos">2B</div>
                            <a title="Player Two" href="/baseball/player/player-two-22222">Player Two</a>
                            <span class="lineup__bats">L</span>
                        </li>
                    </li>
                </ul>
                <ul class="lineup__list is-visit">
                    <li class="lineup__player-highlight mb-0">
                        <div class="lineup__player-highlight-name">
                            <a href="/baseball/player/away-pitcher-67890">Away Pitcher</a>
                            <span class="lineup__throws">L</span>
                        </div>
                        <div class="lineup__player-highlight-stats">
                            4-4&nbsp;4.20 ERA             
                        </div>
                    </li>
                </ul>
            </div>
        </div>  
    """
    soup = daily_lineups.BeautifulSoup(html, "html.parser")
    return soup.select_one("div.lineup__box")


@pytest.mark.unit
@patch("statsapi.get")
def test_get_team_id_by_name(mock_get, mock_get_team_response):
    mock_get.return_value = mock_get_team_response
    team_id_athletics = daily_lineups.get_team_id_by_name("athletics")
    assert team_id_athletics == 133


@pytest.mark.unit
@patch("statsapi.get")
def test_get_team_id_by_name_invalid(mock_get, mock_get_team_response):
    mock_get.return_value = mock_get_team_response
    team_id = daily_lineups.get_team_id_by_name("invalid")
    assert team_id is None


@pytest.mark.unit
def test_extract_teams_from_href():
    href = "/baseball/box-score/reds-vs-guardians-2025-06-07"
    away, home = daily_lineups.extract_teams_from_href(href)
    assert away == "reds"
    assert home == "guardians"


@pytest.mark.unit
def test_extract_teams_from_href_with_long_names():
    href = "/baseball/box-score/blue-jays-vs-red-sox-2025-06-07"
    away, home = daily_lineups.extract_teams_from_href(href)
    assert away == "blue-jays"
    assert home == "red-sox"


@pytest.mark.unit
def test_extract_teams_from_href_invalid():
    href = "/baseball/box-score/invalid"
    away, home = daily_lineups.extract_teams_from_href(href)
    assert away is None
    assert home is None


@pytest.mark.unit
@patch("statsapi.lookup_player")
def test_get_player_id_same_name(
    mock_lookup_player, mock_lookup_player_same_name_response):
    mock_lookup_player.return_value = mock_lookup_player_same_name_response
    result = daily_lineups.get_player_id("Luis Garcia", 119)
    assert result == 472610


@pytest.mark.unit
@patch("statsapi.lookup_player")
def test_get_player_id_invalid_team_id(
    mock_lookup_player, mock_lookup_player_same_name_response):
    mock_lookup_player.return_value = mock_lookup_player_same_name_response
    result = daily_lineups.get_player_id("Luis Garcia", 200)
    assert result is None


@pytest.mark.unit
@patch("statsapi.lookup_player")
def test_get_player_id_invalid_player_name(mock_lookup_player):
    mock_lookup_player.return_value = []
    result = daily_lineups.get_player_id("Luisis Garciacia", 119)
    assert result is None


@pytest.mark.unit
@patch("daily_lineups.get_player_id")
def test_extract_lineup(mock_get_player_id, mock_game_container):
    side_class = "is-home"
    mock_get_player_id.side_effect = [111111, 222222]
    result = daily_lineups.extract_lineup(mock_game_container, side_class, 133)
    expected = [
        {"id": 111111, "name": "Player One"},
        {"id": 222222, "name": "Player Two"}
    ]
    assert result == expected


@pytest.mark.unit
@patch("daily_lineups.extract_name_from_link")
@patch("daily_lineups.get_player_id")
def test_extract_pitcher(
    mock_get_player_id, mock_extract_name_from_link, mock_game_container):
    home_team_id = 111
    away_team_id = 222
    mock_get_player_id.side_effect = [123456, 678910]
    mock_extract_name_from_link.side_effect = ["Home Pitcher", "Away Pitcher"]
    result = daily_lineups.extract_pitchers(
        mock_game_container, home_team_id, away_team_id
    )
    expected = {
        "home_pitcher": {"id": 123456, "name": "Home Pitcher"},
        "away_pitcher": {"id": 678910, "name": "Away Pitcher"},
    }
    assert result == expected


@pytest.mark.unit
@patch("statsapi.schedule")
def test_get_game_id(mock_schedule, mock_schedule_response):
    date = "2025-06-12"
    away_team_id = 120
    home_team_id = 121
    mock_schedule.return_value = mock_schedule_response
    expected = 777544
    result = daily_lineups.get_game_id(date, home_team_id, away_team_id)
    assert result == expected