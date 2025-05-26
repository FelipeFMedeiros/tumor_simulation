"""Configurações e constantes do modelo de simulação tumoral."""

# Estados das células
HEALTHY = 0 
TUMOR = 1
NECROTIC = 2

# Parâmetros do modelo baseados no artigo
GRID_WIDTH = 100
GRID_HEIGHT = 100
INITIAL_RADIUS = 5

# Parâmetros biológicos
R_INIT = 0.0060       # Taxa de crescimento inicial
K = 1e13              # Capacidade de suporte (do artigo)
N0 = 1e9              # População inicial (do artigo)
SPONTANEOUS_RATE = 0.001
MAX_CELL_AGE = 20     # Idade máxima antes da necrose
TREATMENT_FACTOR_INIT = 0.0

# Parâmetros da simulação
MAX_STEPS = 100
ANIMATION_INTERVAL = 100

# Parâmetros visuais
FIGURE_SIZE = (14, 8)
COLORS = ['white', 'red', 'black']  # Healthy, Tumor, Necrotic