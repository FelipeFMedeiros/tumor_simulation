"""Gerenciamento de dados e persistência."""
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from config import COLORS

class DataManager:
    """Classe para gerenciar salvamento e carregamento de dados."""
    
    def save_results(self, simulation):
        """Salva resultados da simulação."""
        if not simulation.steps:
            return
        
        # Garantir comprimentos iguais
        min_len = min(len(simulation.steps), len(simulation.tumor_count), 
                     len(simulation.necrotic_count), len(simulation.growth_rates))
        
        # Criar dataframe
        df = pd.DataFrame({
            'Step': simulation.steps[:min_len],
            'Tumor Cells': simulation.tumor_count[:min_len],
            'Necrotic Cells': simulation.necrotic_count[:min_len],
            'Growth Rate': simulation.growth_rates[:min_len]
        })
        
        try:
            # Salvar CSV
            df.to_csv('tumor_growth_results.csv', index=False)
            print("Dados salvos em tumor_growth_results.csv")
            
            # Salvar imagem final
            self._save_final_image(simulation)
            
        except Exception as e:
            print(f"Erro ao salvar dados: {e}")
    
    def _save_final_image(self, simulation):
        """Salva imagem do estado final."""
        plt.figure(figsize=(8, 8))
        cmap = ListedColormap(COLORS)
        plt.imshow(simulation.tumor_grid.grid, cmap=cmap)
        plt.title(f'Estado Final do Tumor (r={simulation.r:.4f}, '
                 f'Tratamento={simulation.treatment_factor:.2f})')
        plt.colorbar(ticks=[0, 1, 2], label='Tipo Celular')
        plt.savefig('final_tumor_state.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("Imagem final salva em final_tumor_state.png")
    
    def load_results(self, filename='tumor_growth_results.csv'):
        """Carrega resultados salvos."""
        try:
            df = pd.read_csv(filename)
            return df
        except FileNotFoundError:
            print(f"Arquivo {filename} não encontrado.")
            return None
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            return None