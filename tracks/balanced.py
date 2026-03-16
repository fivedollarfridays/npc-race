"""Balanced tracks — mix of straights, fast sweepers, and technical sections."""

# Silverstone: Fast flowing circuit with Maggotts-Becketts complex
SILVERSTONE = {
    "name": "Silverstone",
    "country": "United Kingdom",
    "character": "balanced",
    "laps_default": 5,
    "control_points": [
        (400, 200),  # Start/finish (Wellington Straight)
        (550, 180),  # Copse
        (680, 250),  # Maggotts
        (700, 330),  # Becketts
        (660, 400),  # Chapel
        (550, 420),  # Hangar Straight entry
        (400, 500),  # Stowe
        (300, 550),  # Vale
        (200, 580),  # Club
        (120, 500),  # Abbey
        (80, 380),   # Farm
        (100, 280),  # Village
        (150, 200),  # The Loop
        (250, 160),  # Aintree
        (320, 190),  # Wellington
    ],
}

# Suzuka: Figure-8 crossover, technically demanding
SUZUKA = {
    "name": "Suzuka",
    "country": "Japan",
    "character": "balanced",
    "laps_default": 5,
    "control_points": [
        (300, 200),  # Start/finish
        (450, 150),  # Turn 1-2 (esses entry)
        (550, 100),  # S-curves top
        (650, 170),  # Dunlop curve
        (700, 300),  # Degner 1
        (680, 400),  # Degner 2
        (600, 480),  # Crossover underpass
        (450, 520),  # Hairpin
        (350, 550),  # Spoon entry
        (220, 580),  # Spoon exit
        (130, 500),  # Back straight (under crossover)
        (80, 380),   # 130R
        (100, 280),  # Casio Triangle entry
        (160, 220),  # Casio Triangle exit
    ],
}

# Austin (COTA): Elevation changes with multi-apex turns
AUSTIN = {
    "name": "Austin",
    "country": "United States",
    "character": "balanced",
    "laps_default": 5,
    "control_points": [
        (200, 350),  # Start/finish
        (250, 250),  # Turn 1 climb
        (320, 150),  # Turn 1 apex (hilltop)
        (450, 100),  # Back straight (esses)
        (580, 80),   # Turn 6
        (680, 150),  # Turn 9
        (720, 300),  # Turn 11 hairpin
        (680, 420),  # Turn 12
        (600, 500),  # Turn 15 complex
        (480, 560),  # Turn 16
        (350, 600),  # Turn 18
        (200, 580),  # Turn 19
        (100, 480),  # Turn 20
    ],
}

# Barcelona: Reference circuit for car setup
BARCELONA = {
    "name": "Barcelona",
    "country": "Spain",
    "character": "balanced",
    "laps_default": 5,
    "control_points": [
        (350, 200),  # Start/finish
        (520, 170),  # Turn 1 (Elf)
        (640, 200),  # Turn 3
        (700, 300),  # Turn 4
        (680, 420),  # Turn 5 (slow chicane)
        (600, 500),  # Turn 7
        (480, 560),  # Turn 9
        (350, 600),  # Turn 10 (slow hairpin)
        (220, 550),  # Turn 12
        (120, 450),  # Turn 13
        (80, 330),   # Campsa
        (120, 230),  # Turn 14-15
        (220, 190),  # New chicane
    ],
}

# Bahrain: Desert circuit with heavy braking zones
BAHRAIN = {
    "name": "Bahrain",
    "country": "Bahrain",
    "character": "balanced",
    "laps_default": 5,
    "control_points": [
        (300, 250),  # Start/finish
        (450, 200),  # Turn 1 braking
        (550, 150),  # Turn 1 apex
        (600, 100),  # Turn 2-3
        (680, 180),  # Turn 4
        (720, 320),  # Turn 5-6-7
        (680, 450),  # Turn 8
        (600, 530),  # Turn 9
        (480, 580),  # Turn 10
        (350, 620),  # Turn 11 braking
        (230, 570),  # Turn 12-13
        (130, 460),  # Turn 14
        (80, 350),   # Back straight
    ],
}


BALANCED_TRACKS = {
    "silverstone": SILVERSTONE,
    "suzuka": SUZUKA,
    "austin": AUSTIN,
    "barcelona": BARCELONA,
    "bahrain": BAHRAIN,
}
