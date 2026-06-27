SEASONS = [2021, 2022, 2023, 2024, 2025]

CURRENT_SEASON = 2026

LEAGUE_SETTINGS = {

    # League
    "teams": 12,

    # Starting Lineup
    "qb": 1,
    "rb": 2,
    "wr": 2,
    "te": 1,
    "flex": 1,
    "superflex": 0,

    # Bench
    "bench": 7,

    # Scoring
    "scoring": {
        "passing_yard": 0.04,
        "passing_td": 4,
        "interception": -2,

        "rushing_yard": 0.10,
        "rushing_td": 6,

        "receiving_yard": 0.10,
        "receiving_td": 6,
        "reception": 1,

        "fumble_lost": -2,
    },
}

VALUE_SETTINGS = {

    "replacement_buffer": 0,

    "war_weight": 1.0,

}

PROJECTION_SETTINGS = {

    "regression_weight": 0.35,

    "recent_weight": 0.65,

    "rookie_regression": 0.50,

}