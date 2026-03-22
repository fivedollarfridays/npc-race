"""Power tracks — long straights, high-speed circuits."""

# Monza: Temple of Speed — long straights with tight chicanes
MONZA = {
    "name": "Monza",
    "country": "Italy",
    "character": "power",
    "laps_default": 5,
    "real_length_m": 5793,
    "real_laps": 53,
    "control_points": [
        # Real Monza: massive straights, tight chicanes
        (100, 300),    # S/F line
        (400, 300),    # Main straight mid (DRS)
        (700, 300),    # Main straight continues
        (1000, 300),   # End main straight (~1050m real)
        (1040, 320),   # T1 chicane (sharp 340→80)
        (1020, 350),   # T1 exit
        (950, 450),    # Curva Grande (gentle arc)
        (900, 600),    # Approach Roggia
        (870, 660),    # Roggia chicane
        (890, 700),    # Roggia exit
        (800, 780),    # Lesmo 1
        (700, 820),    # Lesmo 2 exit
        (500, 800),    # Back straight start
        (200, 780),    # Back straight end (~700m real)
        (160, 750),    # Ascari chicane
        (180, 700),    # Ascari exit
        (150, 550),    # Parabolica approach
        (120, 400),    # Parabolica (fast sweeper)
    ],
    "drs_zones": [(0.0, 0.15), (0.55, 0.68)],
}

# Baku: Street circuit with castle section and massive straight
BAKU = {
    "name": "Baku",
    "country": "Azerbaijan",
    "character": "power",
    "laps_default": 5,
    "real_length_m": 6003,
    "real_laps": 51,
    "control_points": [
        (100, 600),  # Start/finish
        (100, 400),  # Long straight north
        (100, 200),  # Turn 1 approach
        (150, 120),  # Castle section entry
        (250, 100),  # Castle hairpin
        (350, 80),   # Narrow castle streets
        (450, 100),  # Castle exit
        (550, 150),  # Turn 8
        (650, 250),  # Waterfront approach
        (700, 350),  # Turn 12
        (700, 500),  # Back straight south
        (650, 600),  # Turn 16 hairpin
        (500, 630),  # Turn 18
        (300, 640),  # Final sector
    ],
}

# Jeddah: Ultra-fast street circuit with sweeping curves
JEDDAH = {
    "name": "Jeddah",
    "country": "Saudi Arabia",
    "character": "power",
    "laps_default": 5,
    "real_length_m": 6174,
    "real_laps": 50,
    "control_points": [
        (200, 600),  # Start/finish
        (100, 500),  # Turn 1
        (80, 350),   # Long left sweep
        (100, 200),  # Turn 4
        (200, 100),  # Fast kink
        (350, 80),   # Turn 7-8 complex
        (500, 100),  # Turn 10
        (600, 200),  # High-speed esses
        (650, 350),  # Turn 13 wall
        (700, 450),  # Back straight entry
        (720, 550),  # Turn 22
        (650, 620),  # Turn 25
        (450, 640),  # Final chicane
        (300, 630),  # Turn 27
    ],
}

# Spa: Legendary Ardennes circuit with Eau Rouge and long Kemmel straight
SPA = {
    "name": "Spa",
    "country": "Belgium",
    "character": "power",
    "laps_default": 5,
    "real_length_m": 7004,
    "real_laps": 44,
    "control_points": [
        (200, 550),  # La Source hairpin
        (300, 600),  # Eau Rouge entry (downhill)
        (350, 640),  # Eau Rouge bottom
        (400, 580),  # Raidillon climb
        (500, 500),  # Kemmel straight
        (650, 450),  # Les Combes
        (700, 380),  # Malmedy
        (680, 280),  # Rivage
        (600, 200),  # Pouhon double left
        (500, 150),  # Fagnes chicane
        (350, 100),  # Stavelot
        (250, 150),  # Paul Frere curve
        (180, 250),  # Blanchimont
        (120, 380),  # Bus Stop chicane
        (150, 480),  # Pit entry
    ],
    "drs_zones": [(0.72, 0.88)],
}


POWER_TRACKS = {
    "monza": MONZA,
    "baku": BAKU,
    "jeddah": JEDDAH,
    "spa": SPA,
}
