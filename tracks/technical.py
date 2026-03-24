"""Technical tracks — tight corners, low-speed precision."""

# Monaco: Tight streets of Monte Carlo with hairpin and tunnel
MONACO = {
    "name": "Monaco",
    "country": "Monaco",
    "character": "technical",
    "laps_default": 78,
    "real_length_m": 3337,
    "real_laps": 78,
    "control_points": [
        (400, 100),  # Start/finish
        (550, 80),   # Sainte Devote
        (650, 150),  # Beau Rivage climb
        (700, 300),  # Massenet
        (680, 380),  # Casino Square
        (600, 420),  # Mirabeau
        (550, 500),  # Grand Hotel hairpin
        (500, 550),  # Portier
        (350, 580),  # Tunnel entry
        (200, 560),  # Tunnel exit / chicane
        (150, 480),  # Tabac
        (100, 380),  # Swimming Pool complex
        (120, 280),  # Rascasse
        (200, 200),  # Anthony Noghes
        (300, 140),  # Pit straight approach
    ],
}

# Singapore: Night race street circuit
SINGAPORE = {
    "name": "Singapore",
    "country": "Singapore",
    "character": "technical",
    "laps_default": 62,
    "real_length_m": 5063,
    "real_laps": 62,
    "control_points": [
        (300, 600),  # Start/finish
        (150, 580),  # Turn 1
        (80, 500),   # Turn 3
        (100, 380),  # Memorial turn
        (150, 280),  # Turn 5
        (250, 200),  # Turn 7 hairpin
        (380, 150),  # Singapore Sling
        (500, 100),  # Turn 10
        (620, 150),  # Turn 11
        (700, 280),  # Turn 14
        (680, 400),  # Turn 17
        (620, 500),  # Turn 19
        (500, 580),  # Anderson Bridge
        (400, 620),  # Turn 23
    ],
}

# Zandvoort: Banked turns in the Dutch dunes
ZANDVOORT = {
    "name": "Zandvoort",
    "country": "Netherlands",
    "character": "technical",
    "laps_default": 72,
    "real_length_m": 4259,
    "real_laps": 72,
    "control_points": [
        (350, 150),  # Start/finish
        (500, 120),  # Tarzan banked entry
        (600, 170),  # Tarzan exit
        (650, 280),  # Gerlachbocht
        (680, 400),  # Hugenholtz
        (640, 500),  # Scheivlak
        (550, 560),  # Marlboro (fast kink)
        (400, 600),  # Renault hairpin
        (280, 580),  # Vodafone chicane
        (180, 500),  # Hans Ernst
        (100, 380),  # Kumho
        (80, 250),   # Arie Luyendyk banked
        (150, 160),  # Last corner exit
    ],
}


TECHNICAL_TRACKS = {
    "monaco": MONACO,
    "singapore": SINGAPORE,
    "zandvoort": ZANDVOORT,
}
