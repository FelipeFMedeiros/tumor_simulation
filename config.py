"""Configurações e constantes do modelo de simulação tumoral."""
import numpy as np

# Estados das células
HEALTHY, TUMOR, NECROTIC = 0,1,2

# Parâmetros do modelo baseados no artigo
GRID_WIDTH = 100
GRID_HEIGHT = 100
INITIAL_RADIUS = 3


# Parâmetros biológicos
K = 1e13           # Capacidade de carga máxima
N0 = 1e9           # Tumor inicial
r = 0.0060         # Constante de crescimento
gamma = 0.04       # Efeito da droga
c0 = 0.04          # Concentração no organismo
#S = 0              # if True -> há tratamento
MAX_STEPS = 100    # Tempo máximo (semanas)
#dt = 1            # Passos no tempo (instantes)
MAX_CELL_AGE = 20
SPONTANEOUS_RATE = 0.001



# Parâmetros da simulação
ANIMATION_INTERVAL = 100

# Parâmetros visuais
FIGURE_SIZE = (14, 8)
COLORS = ['white', 'red', 'black']  # Healthy, Tumor, Necrotic