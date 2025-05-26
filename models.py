"""Modelos e lógica de simulação tumoral."""
import numpy as np
from config import *

class TumorGrid:
    """Classe para gerenciar o grid da simulação tumoral."""
    
    def __init__(self):
        self.grid = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=int)
        self.ages = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=int)
        self.initial_tumor_count = 0
        self.scale_factor = 1
        
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
        
        # Calcular fator de escala
        self.scale_factor = N0 / self.initial_tumor_count if self.initial_tumor_count > 0 else 1
        return self.initial_tumor_count
    
    def get_tumor_density(self, x, y, radius=1):
        """Calcula densidade tumoral local."""
        x_min, x_max = max(0, x-radius), min(GRID_WIDTH, x+radius+1)
        y_min, y_max = max(0, y-radius), min(GRID_HEIGHT, y+radius+1)
        
        subgrid = self.grid[y_min:y_max, x_min:x_max]
        total_cells = (y_max - y_min) * (x_max - x_min)
        tumor_cells = np.sum(subgrid == TUMOR) + np.sum(subgrid == NECROTIC)
        
        return tumor_cells / total_cells if total_cells > 0 else 0
    
    def get_healthy_neighbors(self, x, y):
        """Retorna vizinhos saudáveis de uma célula."""
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
        self.r = R_INIT
        self.treatment_factor = TREATMENT_FACTOR_INIT
        self.tumor_count = []
        self.necrotic_count = []
        self.steps = []
        self.growth_rates = []
        
    def reset(self):
        """Reinicia a simulação."""
        self.tumor_grid.initialize()
        self.r = R_INIT
        self.treatment_factor = TREATMENT_FACTOR_INIT
        self.tumor_count = []
        self.necrotic_count = []
        self.steps = []
        self.growth_rates = []
    
    def update_step(self, step):
        """Atualiza um passo da simulação."""
        new_grid = self.tumor_grid.grid.copy()
        
        # Processar cada célula
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.tumor_grid.grid[y, x] == TUMOR:
                    self._process_tumor_cell(x, y, new_grid)
                elif self.tumor_grid.grid[y, x] == HEALTHY:
                    self._process_healthy_cell(x, y, new_grid)
        
        # Atualizar grid
        self.tumor_grid.grid = new_grid
        
        # Calcular estatísticas
        self._calculate_statistics(step)
    
    def _process_tumor_cell(self, x, y, new_grid):
        """Processa uma célula tumoral."""
        # Envelhecer
        self.tumor_grid.ages[y, x] += 1
        
        # NECROSE BASEADA APENAS NO TRATAMENTO (Modelo de Gompertz)
        if self.treatment_factor > 0:
            # Probabilidade de necrose proporcional ao tratamento
            # Células mais velhas são mais suscetíveis ao tratamento
            age_factor = min(float(self.tumor_grid.ages[y, x]) / MAX_CELL_AGE, 1.0)
            tumor_density = self.tumor_grid.get_tumor_density(x, y)
            
            # Probabilidade de necrose por tratamento
            p_necrosis = self.treatment_factor * 0.1 * (1 + age_factor) * (0.5 + tumor_density/2)
            
            if np.random.random() < p_necrosis:
                new_grid[y, x] = NECROTIC
                return
        
        # Tentar divisão (reduzida pelo tratamento)
        neighbors = self.tumor_grid.get_healthy_neighbors(x, y)
        if neighbors:
            tumor_density = self.tumor_grid.get_tumor_density(x, y)
            
            # Taxa de crescimento baseada no modelo de Gompertz
            # Reduzida pelo tratamento e pela densidade
            p_division = (self.r * (1 - np.log(tumor_density + 1e-10)/np.log(1.0 + 1e-10)) * 
                         (1 - self.treatment_factor))
            
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
        tumor_cells = np.sum(self.tumor_grid.grid == TUMOR)
        necrotic_cells = np.sum(self.tumor_grid.grid == NECROTIC)
        
        # Aplicar escala
        self.tumor_count.append(tumor_cells * self.tumor_grid.scale_factor)
        self.necrotic_count.append(necrotic_cells * self.tumor_grid.scale_factor)
        self.steps.append(step)
        
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
        if len(self.tumor_count) > 0 and self.tumor_count[-1] <= 0:
            return True, "Tumor eliminado"
        
        # Se estabilizou por um tempo
        if self.is_stabilized():
            return True, "Simulação estabilizada"
        
        # Se atingiu capacidade máxima
        if len(self.tumor_count) > 0 and self.tumor_count[-1] > K * 0.9:
            return True, "Capacidade máxima atingida"
        
        return False, "Continuando..."