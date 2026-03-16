"""Character tracks — unique layouts with distinctive features."""

# Interlagos: Counter-clockwise with elevation, Senna S
INTERLAGOS = {
    "name": "Interlagos",
    "country": "Brazil",
    "character": "character",
    "laps_default": 6,
    "control_points": [
        (500, 200),  # Start/finish
        (620, 160),  # Senna S entry (downhill)
        (680, 220),  # Senna S bottom
        (650, 310),  # Turn 3
        (580, 400),  # Descida do Lago
        (500, 480),  # Turn 6
        (380, 530),  # Ferradura
        (270, 560),  # Turn 8
        (180, 500),  # Pinheirinho
        (100, 400),  # Bico de Pato
        (120, 280),  # Junção
        (200, 200),  # Subida dos Boxes (uphill)
        (350, 170),  # Back to start
    ],
}

# Imola: Old-school with elevation and Tamburello
IMOLA = {
    "name": "Imola",
    "country": "Italy",
    "character": "character",
    "laps_default": 6,
    "control_points": [
        (350, 300),  # Start/finish
        (500, 280),  # Tamburello approach
        (620, 250),  # Tamburello
        (700, 200),  # Villeneuve chicane
        (680, 130),  # Tosa hairpin
        (580, 100),  # Piratella
        (450, 80),   # Acque Minerali
        (340, 120),  # Variante Alta
        (250, 200),  # Fast downhill
        (180, 320),  # Rivazza 1
        (120, 440),  # Rivazza 2
        (200, 530),  # Variante Bassa
        (320, 500),  # Final chicane
        (400, 400),  # Approach to start
    ],
}

# Melbourne: Semi-street circuit around Albert Park lake
MELBOURNE = {
    "name": "Melbourne",
    "country": "Australia",
    "character": "character",
    "laps_default": 5,
    "control_points": [
        (400, 600),  # Start/finish
        (550, 580),  # Turn 1
        (650, 520),  # Turn 3
        (700, 400),  # Turn 6
        (680, 280),  # Turn 9 (fast chicane)
        (600, 180),  # Turn 11
        (450, 100),  # Turn 12
        (300, 80),   # Turn 13
        (180, 150),  # Turn 14
        (100, 280),  # Turn 15
        (80, 420),   # Lake section
        (150, 540),  # Final turns
        (280, 610),  # Approach to start
    ],
}

# Montreal: Island circuit with Wall of Champions
MONTREAL = {
    "name": "Montreal",
    "country": "Canada",
    "character": "character",
    "laps_default": 6,
    "control_points": [
        (250, 400),  # Start/finish
        (350, 350),  # Turn 1-2 chicane
        (450, 280),  # Turn 3
        (550, 200),  # Island straight
        (650, 130),  # Turn 6 hairpin
        (700, 220),  # Turn 7
        (720, 350),  # Back straight
        (700, 470),  # Turn 10
        (620, 550),  # L'Epingle hairpin
        (500, 580),  # Droit du Casino
        (380, 600),  # Wall of Champions approach
        (200, 560),  # Final chicane
        (130, 470),  # Pit entry
    ],
}

# Mugello: Tuscany — fast sweepers through rolling hills
MUGELLO = {
    "name": "Mugello",
    "country": "Italy",
    "character": "character",
    "laps_default": 5,
    "control_points": [
        (300, 300),  # Start/finish
        (450, 250),  # San Donato
        (580, 200),  # Luco-Poggio Secco
        (680, 150),  # Materassi
        (720, 280),  # Borgo San Lorenzo
        (700, 420),  # Casanova-Savelli
        (620, 520),  # Arrabbiata 1
        (500, 580),  # Arrabbiata 2
        (350, 600),  # Scarperia
        (200, 560),  # Palagio
        (100, 450),  # Correntaio
        (80, 340),   # Biondetti
    ],
}

# Lusail: Desert speed with flowing curves
LUSAIL = {
    "name": "Lusail",
    "country": "Qatar",
    "character": "character",
    "laps_default": 5,
    "control_points": [
        (350, 200),  # Start/finish
        (500, 160),  # Turn 1 long left
        (630, 130),  # Turn 4
        (710, 200),  # Turn 6
        (720, 340),  # Turn 8
        (680, 460),  # Turn 10
        (560, 540),  # Turn 12 hairpin
        (420, 580),  # Turn 13
        (280, 600),  # Turn 14
        (150, 530),  # Turn 15
        (80, 400),   # Turn 16 complex
        (100, 280),  # Back to main straight
    ],
}

# Hungaroring: Tight, twisty, overtaking-difficult
HUNGARORING = {
    "name": "Hungaroring",
    "country": "Hungary",
    "character": "character",
    "laps_default": 7,
    "control_points": [
        (350, 150),  # Start/finish
        (500, 120),  # Turn 1 braking
        (600, 170),  # Turn 2
        (680, 270),  # Turn 3-4
        (700, 400),  # Turn 5
        (650, 500),  # Turn 6
        (550, 560),  # Turn 7-8
        (400, 600),  # Turn 9
        (270, 580),  # Turn 10-11
        (150, 500),  # Turn 12
        (80, 380),   # Turn 13
        (100, 250),  # Turn 14
        (200, 170),  # Final chicane
    ],
}

# Shanghai: Distinctive snail-shell Turn 1-2-3
SHANGHAI = {
    "name": "Shanghai",
    "country": "China",
    "character": "character",
    "laps_default": 5,
    "control_points": [
        (300, 300),  # Start/finish
        (420, 260),  # Turn 1 entry (spiral)
        (500, 200),  # Turn 2 inner spiral
        (520, 140),  # Turn 3 spiral exit
        (600, 100),  # Turn 4
        (700, 180),  # Turn 6 hairpin
        (720, 320),  # Back straight north
        (700, 460),  # Turn 8
        (620, 540),  # Turn 9-10
        (480, 580),  # Turn 11
        (330, 600),  # Turn 13 braking
        (200, 540),  # Turn 14 hairpin
        (100, 420),  # Back straight south
        (120, 320),  # Final turn
    ],
}


CHARACTER_TRACKS = {
    "interlagos": INTERLAGOS,
    "imola": IMOLA,
    "melbourne": MELBOURNE,
    "montreal": MONTREAL,
    "mugello": MUGELLO,
    "lusail": LUSAIL,
    "hungaroring": HUNGARORING,
    "shanghai": SHANGHAI,
}
