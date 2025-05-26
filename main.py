"""Arquivo principal para execução da simulação tumoral."""
from visualization import TumorVisualizer

def main():
    """Função principal."""
    print("Iniciando simulação do crescimento tumoral...")
    
    # Criar e executar visualizador
    visualizer = TumorVisualizer()
    visualizer.run()

if __name__ == "__main__":
    main()