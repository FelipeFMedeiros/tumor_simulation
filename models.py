"""Modelos e lógica de simulação tumoral."""
import numpy as np
from fontTools.merge.util import current_time

from config import *

class TumorGrid:
    """Classe para gerenciar o grid da simulação tumoral."""
    
    def __init__(self):
        self.grid = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=int)
        self.ages = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=int)
        self.initial_tumor_count = 0
        self.scale_factor = 1
        self.real_world_scale = N0 #Fator de escala para o mundo real
        
    def initialize(self):
        """Inicializa o grid com tumor central."""
        self.grid = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=int)
        self.ages = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=int)
        
        center_x, center_y = GRID_WIDTH // 2, GRID_HEIGHT // 2
        self.initial_tumor_count = 0
        
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                if dist <= INITIAL_RADIUS:
                    self.grid[y, x] = TUMOR
                    self.initial_tumor_count += 1
        
        # =================Calcular FATOR de escala=================
        self.scale_factor = N0 / self.initial_tumor_count if self.initial_tumor_count > 0 else 1
        print(f"Células tumorais iniciais: {self.initial_tumor_count} (≈ {self.scale_factor:.2e} células reais)")
        return self.initial_tumor_count

    '''FUNÇÃO NOVA TESTANDO'''
    def get_real_world_count(self):
        """Retorna a estimativa de células no mundo real."""
        current_tumor = np.sum(self.grid == TUMOR)
        current_necrotic = np.sum(self.grid == NECROTIC)
        return {
            'tumor_real': current_tumor * self.scale_factor,
            'necrotic_real': current_necrotic * self.scale_factor,
            'total_real': (current_tumor + current_necrotic) * self.scale_factor,
            #'current_real_count' : self.get_real_world_count()
        }

    def get_tumor_density(self, x, y, radius=1):
        """Calcula densidade tumoral local."""
                            #LimEsq     Não passa da borda    LimDir
        x_min, x_max = max(0, x-radius), min(GRID_WIDTH, x+radius+1)
        y_min, y_max = max(0, y-radius), min(GRID_HEIGHT, y+radius+1)

        subgrid = self.grid[y_min:y_max, x_min:x_max]
        total_cells = (y_max - y_min) * (x_max - x_min)
        tumor_cells = np.sum(subgrid == TUMOR) + np.sum(subgrid == NECROTIC)

        return tumor_cells / total_cells# if total_cells > 0 else 0

    def get_healthy_neighbors(self, x, y):
        """Retorna vizinhos saudáveis de uma célula."""
        #Utiliza a ideia de vizinhança de Moore
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT and
                    self.grid[ny, nx] == HEALTHY):
                    neighbors.append((nx, ny))
        return neighbors

    def count_tumor_neighbors(self, x, y):
        """Conta vizinhos tumorais de uma célula."""
        count = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT and
                    self.grid[ny, nx] == TUMOR):
                    count += 1
        return count

class TumorSimulation:
    """Classe principal para simulação do crescimento tumoral."""

    def __init__(self):
        self.tumor_grid = TumorGrid()
        self.gamma = gamma
        self.r = r
        self.c0 = c0
        self.treatment_factor = 0
        self.tumor_count = []
        self.necrotic_count = []
        self.steps = []
        self.growth_rates = []
        self.tumor_grid.initialize()
        self.current_time = 0  # Rastreia o tempo na
        # garante maior precisão usando com exponencial

    def reset(self):
        self.tumor_grid.initialize()
        self.gamma = gamma
        self.r = r
        self.c0 = c0
        self.treatment_factor = 0
        self.tumor_count = []
        self.necrotic_count = []
        self.steps = []
        self.growth_rates = []
        self.current_time = 0

    #New function
    def calculate_drug_concentration(self, t):
        time_in_days = t/24
        #teste
        print(f"Calculando concentração com treatment_factor={self.treatment_factor:}")  # Debug

        #====Calcula c(t) = c₀ * S * t * e^(-rt)====
        return self.c0 * self.treatment_factor * time_in_days * np.exp(-self.r * time_in_days)

    def update_step(self, step):
        #Atualiza um passo da simulação com efeito da droga.
        self.current_time +=1


        #DRUG EFFECT
        drug_effect = self.gamma * self.calculate_drug_concentration(self.current_time)

        new_grid = self.tumor_grid.grid.copy()
        #evita modificar o estado original enquanto processa células

        # Processar cada célula
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.tumor_grid.grid[y, x] == TUMOR:

                    self._process_tumor_cell(x, y, new_grid, drug_effect)

                elif self.tumor_grid.grid[y, x] == HEALTHY:

                    self._process_healthy_cell(x, y, new_grid)

        # Atualizar grid
        self.tumor_grid.grid = new_grid

        # Calcular estatísticas
        self._calculate_statistics(step)

    def _process_tumor_cell(self, x, y, new_grid, drug_effect):
        #====Processa uma célula tumoral. com o efeito do medicamento (ou não)====

        # Envelhecer
        self.tumor_grid.ages[y, x] += 1

        # NECROSE BASEADA APENAS NO TRATAMENTO (Modelo de Gompertz)
        if self.treatment_factor == 1: #S varia APENAS de 0 a 1
            # Probabilidade de necrose proporcional ao tratamento
            # Células mais velhas são mais suscetíveis ao tratamento
            age_factor = min(float(self.tumor_grid.ages[y, x]) / MAX_CELL_AGE, 1.0)
            tumor_density = self.tumor_grid.get_tumor_density(x, y)

                # Probabilidade de necrose por tratamento
                        #=======EQUAÇÃO DO TRATAMENTO=======


            p_necrosis = (self.treatment_factor * 0.01 * (1 + 0.5* age_factor) * (0.5 + tumor_density) + drug_effect *0.1)  # Efeito direto do medicamento
            '''TESTE'''
            print(f"Processando célula com treatment_factor={self.treatment_factor}, drug_effect={drug_effect}")  # Debug

            if np.random.random() < p_necrosis:
                new_grid[y, x] = NECROTIC
                return

        # Tentar divisão (reduzida pelo tratamento)
        neighbors = self.tumor_grid.get_healthy_neighbors(x, y)
        if neighbors:
            tumor_density = self.tumor_grid.get_tumor_density(x, y)

            global_density = np.sum(self.tumor_grid.grid == TUMOR) / (GRID_WIDTH * GRID_HEIGHT)
            #global_density = max(global_density, 1e-10)

            #=====Taxa de crescimento baseada no modelo de Gompertz=====

                        # Reduzida pelo tratamento e pela densidade
                                                            #Valor mto pequeno evitar log(0) e suavizir o impactor para density =0
            #p_division = (self.r * (1 - np.log(tumor_density + 1e-10)/ np.log(1.0+1e-10)) - drug_effect)
            p_division = self.r * - np.log(global_density)- drug_effect
            #===========================================================

            if np.random.random() < p_division:
                nx, ny = neighbors[np.random.randint(0, len(neighbors))]
                new_grid[ny, nx] = TUMOR

    def _process_healthy_cell(self, x, y, new_grid):
        """Processa uma célula saudável."""
        tumor_neighbors = self.tumor_grid.count_tumor_neighbors(x, y)

        # Transformação espontânea reduzida pelo tratamento
        if (tumor_neighbors > 0 and
            np.random.random() < SPONTANEOUS_RATE * (1 - self.treatment_factor)):
            new_grid[y, x] = TUMOR

    def _calculate_statistics(self, step):
        """Calcula estatísticas do passo atual."""
        real_counts = self.tumor_grid.get_real_world_count()

        # Aplicar escala
        self.tumor_count.append(real_counts['tumor_real'])
        self.necrotic_count.append(real_counts['necrotic_real'])
        self.steps.append(step)

        #Log dos valores reais
        print(f"\nEstatísticas no passo {step}:")
        print(f"Células tumorais: {int(real_counts['tumor_real']):,}")
        print(f"Células necróticas: {int(real_counts['necrotic_real']):,}")
        print(f"Total de células: {int(real_counts['total_real']):,}")

        # Calcular taxa de crescimento
        if len(self.tumor_count) > 1 and self.tumor_count[-2] > 0:
            growth_rate = (self.tumor_count[-1] - self.tumor_count[-2]) / self.tumor_count[-2]
            self.growth_rates.append(growth_rate)
        else:
            self.growth_rates.append(0)

    def is_stabilized(self, window_size=10, threshold=0.001):
        """Verifica se a simulação estabilizou."""
        if len(self.growth_rates) < window_size:
            return False

        # Verificar se as últimas taxas de crescimento são pequenas
        recent_rates = self.growth_rates[-window_size:]
        avg_growth = np.mean(np.abs(recent_rates))

        return avg_growth < threshold

    def has_converged(self):
        """Verifica se a simulação convergiu (critérios de parada)."""
        # Se não há células tumorais, a simulação acabou
        if len(self.tumor_count) > 0 >= self.tumor_count[-1]:
            return True, "Tumor eliminado"

        # Se estabilizou por um tempo
        if self.is_stabilized():
            return True, "Simulação estabilizada"

        # Se atingiu capacidade máxima
        if len(self.tumor_count) > 0 and self.tumor_count[-1] > K * 0.9:
            return True, "Capacidade máxima atingida"

        return False, "Continuando..."
