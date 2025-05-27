"""Interface gráfica e visualização da simulação."""
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import matplotlib.animation as animation
from matplotlib.widgets import Slider, Button
import numpy as np
from config import *
from models import TumorSimulation
from itertools import count


class TumorVisualizer:
    """Classe para visualização da simulação tumoral."""
    
    def __init__(self):
        self.simulation = TumorSimulation()
        self.simulation.reset()
        
        self.is_running = False
        self.current_frame = 0
        self.ani = None
        
        self._setup_figure()
        self._setup_plots()
        self._setup_controls()
        self._connect_events()
    
    def _setup_figure(self):
        """Configura a figura principal."""
        self.fig = plt.figure(figsize=FIGURE_SIZE)
        plt.subplots_adjust(left=0.05, bottom=0.25, right=0.95, top=0.9, wspace=0.3)
        
        # Layout com 3 gráficos
        self.ax1 = plt.subplot2grid((2, 2), (0, 0), rowspan=2, colspan=1)  # Grid
        self.ax2 = plt.subplot2grid((2, 2), (0, 1), rowspan=1, colspan=1)  # População
        self.ax3 = plt.subplot2grid((2, 2), (1, 1), rowspan=1, colspan=1)  # Crescimento
    
    def _setup_plots(self):
        """Configura os gráficos."""
        # Grid do tumor
        self.cmap = ListedColormap(COLORS)
        self.im = self.ax1.imshow(self.simulation.tumor_grid.grid, cmap=self.cmap, vmin=0, vmax=2)
        self.ax1.set_title('Simulação do Crescimento Tumoral')
        self.ax1.set_xticks([])
        self.ax1.set_yticks([])
        
        # Gráfico de população
        self.line_tumor, = self.ax2.plot([], [], 'r-', linewidth=2, label='Células Tumorais')
        self.line_necrotic, = self.ax2.plot([], [], 'k-', linewidth=2, label='Células Necróticas')
        self.ax2.set_xlabel('Passos de Tempo')
        self.ax2.set_ylabel('Contagem de Células (escala log)')
        self.ax2.set_title('População Celular ao Longo do Tempo')
        self.ax2.set_yscale('log')
        self.ax2.grid(True)
        self.ax2.legend()
        self.ax2.set_xlim(0, MAX_STEPS * 2)  # Deixar espaço para simulações mais longas
        self.ax2.set_ylim(N0/10, K*1.1) #?
        
        # Gráfico de crescimento
        self.line_growth, = self.ax3.plot([], [], 'g-', linewidth=2)
        self.ax3.set_xlabel('Passos de Tempo')
        self.ax3.set_ylabel('Taxa de Crescimento')
        self.ax3.set_title('Taxa de Crescimento Instantânea')
        self.ax3.grid(True)
        self.ax3.set_xlim(0, MAX_STEPS * 2)  # Deixar espaço para simulações mais longas
        self.ax3.set_ylim(-0.1, 0.5)
    
    def _setup_controls(self):
        """Configura controles interativos."""
        # Status
        self.status_text = plt.figtext(0.5, 0.02, "Clique em 'Iniciar' para começar", 
                                      ha="center", fontsize=10, 
                                      bbox=dict(facecolor='lightgrey', alpha=0.5))
        
        # Frame counter
        self.frame_text = plt.figtext(0.05, 0.02, "Frame: 0", 
                                     ha="left", fontsize=10)
        
        # Estatísticas
        self.stats_text = plt.figtext(0.95, 0.02, "Tumor: 0 | Necrótico: 0", 
                                     ha="right", fontsize=10)
        
        # Botões simplificados
        button_width = 0.15
        button_height = 0.04
        button_y = 0.07
        
        # Botão Play/Pause
        ax_play = plt.axes((0.35, button_y, button_width, button_height))
        self.play_button = Button(ax_play, 'INICIAR', color='lightgreen', hovercolor='green')
        
        # Botão Reset
        ax_reset = plt.axes((0.55, button_y, button_width, button_height))
        self.reset_button = Button(ax_reset, 'RESET', color='lightblue', hovercolor='blue')
        
        # Sliders
        ax_treatment = plt.axes((0.15, 0.17, 0.7, 0.03), facecolor='lightgoldenrodyellow')
        self.treatment_slider = Slider(
            ax=ax_treatment, label='Fator de Tratamento',
            valmin=0.0, valmax=1.0, valinit=S, color='green'
        )
        
        ax_r = plt.axes((0.15, 0.13, 0.7, 0.03), facecolor='lightgoldenrodyellow')
        self.r_slider = Slider(
            ax=ax_r, label='Taxa de Crescimento (r)',
            valmin=0.001, valmax=0.02, valinit=r, color='blue'
        )
    
    def _connect_events(self):
        """Conecta eventos aos controles."""
        self.r_slider.on_changed(self._on_parameter_change)
        self.treatment_slider.on_changed(self._on_parameter_change)
        self.play_button.on_clicked(self._toggle_simulation)
        self.reset_button.on_clicked(self._reset_simulation)
        self.fig.canvas.mpl_connect('close_event', self._on_close)
    
    def _on_parameter_change(self, val):
        """Chamado quando um slider muda - reinicia a simulação."""
        # Atualizar parâmetros
        self.simulation.r = float(self.r_slider.val)
        self.simulation.treatment_factor = float(self.treatment_slider.val)
        
        # Reiniciar simulação automaticamente
        self._reset_simulation_data()
        self._update_title()
        
        print(f"Parâmetros atualizados - r: {self.simulation.r:.4f}, tratamento: {self.simulation.treatment_factor:.2f}")
    
    def _update_title(self):
        """Atualiza título da figura."""
        title = f'Simulação do Modelo de Gompertz'
        plt.suptitle(title, fontsize=14, fontweight= 'bold')
        self.fig.canvas.draw_idle()
    
    def _toggle_simulation(self, event):
        """Inicia/pausa simulação."""
        if not self.is_running:
            self._start_simulation()
        else:
            self._pause_simulation()
    
    def _start_simulation(self):
        """Inicia a simulação."""
        print("Iniciando simulação...")
        self.is_running = True
        self.play_button.label.set_text('PAUSAR')
        self.status_text.set_text("Simulação em andamento...")

        #Teste para frames.
        frame_source = iter(self._frame_generator()) #É um iterador

        # Criar animação - sem limite de frames fixo
        self.ani = animation.FuncAnimation(
            self.fig, self._update_frame, 
            interval=ANIMATION_INTERVAL,
            blit=False,
            frames=frame_source,
            repeat=False
        )
        
        self.fig.canvas.draw_idle()
    
    def _frame_generator(self):
        """Gerador de frames que continua até a simulação convergir."""
        frame = self.current_frame
        while frame < MAX_STEPS * 5:  # Limite máximo de segurança (5x o original)
            yield frame
            frame += 1
    
    def _pause_simulation(self):
        """Pausa a simulação."""
        print("Pausando simulação...")
        self.is_running = False
        self.play_button.label.set_text('CONTINUAR')
        self.status_text.set_text("Simulação pausada")
        
        if self.ani:
            self.ani.event_source.stop()
            self.ani = None
        
        self.fig.canvas.draw_idle()
    
    def _reset_simulation(self, event):
        """Reinicia simulação completamente."""
        print("Resetando simulação...")
        
        # Parar animação
        if self.ani:
            self.ani.event_source.stop()
            self.ani = None
        
        # Reset completo
        self.is_running = False
        self.current_frame = 0
        
        # Resetar dados da simulação
        self._reset_simulation_data()
        
        # Atualizar interface
        self.play_button.label.set_text('INICIAR')
        self.status_text.set_text("Simulação reiniciada. Clique em 'Iniciar'")
        self.frame_text.set_text("Frame: 0")
        self.stats_text.set_text("Tumor: 0 | Necrótico: 0")
        
        self.fig.canvas.draw_idle()
    
    def _reset_simulation_data(self):
        """Reseta apenas os dados da simulação."""
        # Resetar simulação
        self.simulation.reset()
        
        # Aplicar parâmetros atuais dos sliders
        self.simulation.r = float(self.r_slider.val)
        self.simulation.treatment_factor = float(self.treatment_slider.val)
        
        # Limpar gráficos
        self.line_tumor.set_data([], [])
        self.line_necrotic.set_data([], [])
        self.line_growth.set_data([], [])
        
        # Atualizar grid visual
        self.im.set_array(self.simulation.tumor_grid.grid)
        
        # Resetar frame
        self.current_frame = 0
    
    def _update_frame(self, frame):
        """Atualiza frame da animação."""
        if not self.is_running:
            return [self.im, self.line_tumor, self.line_necrotic, self.line_growth]
        
        self.current_frame = frame
        
        # Atualizar simulação
        self.simulation.update_step(frame)
        
        # Atualizar visualizações
        self.im.set_array(self.simulation.tumor_grid.grid)
        
        # Atualizar gráficos
        if self.simulation.steps:
            self.line_tumor.set_data(self.simulation.steps, self.simulation.tumor_count)
            self.line_necrotic.set_data(self.simulation.steps, self.simulation.necrotic_count)
            
            # Gráfico de crescimento
            if len(self.simulation.growth_rates) > 0:
                growth_steps = self.simulation.steps[:len(self.simulation.growth_rates)]
                self.line_growth.set_data(growth_steps, self.simulation.growth_rates)
        
        # Ajustar limites dinamicamente
        self._adjust_plot_limits()
        
        # Atualizar textos de status
        tumor_count = np.sum(self.simulation.tumor_grid.grid == TUMOR)
        necrotic_count = np.sum(self.simulation.tumor_grid.grid == NECROTIC)
        
        self.frame_text.set_text(f"Frame: {frame}")
        self.stats_text.set_text(f"Tumor: {tumor_count} | Necrótico: {necrotic_count}")
        
        # Verificar convergência da simulação
        converged, reason = self.simulation.has_converged()
        if converged or frame >= MAX_STEPS * 5:  # Limite de segurança
            print(f"Simulação concluída: {reason}")
            self.is_running = False
            self.status_text.set_text(f"Simulação concluída: {reason}")
            self.play_button.label.set_text('INICIAR')
            if self.ani:
                self.ani.event_source.stop()
                self.ani = None
        
        return [self.im, self.line_tumor, self.line_necrotic, self.line_growth]
    
    def _adjust_plot_limits(self):
        """Ajusta limites dos gráficos dinamicamente."""
        if not self.simulation.steps:
            return
            
        steps = self.simulation.steps
        growth_rates = self.simulation.growth_rates
        max_step = max(steps) if steps else 0
        
        # Ajustar limites X dinamicamente
        x_limit = max(max_step + 20, MAX_STEPS)  # Sempre um pouco além do frame atual
        self.ax2.set_xlim(0, x_limit)
        self.ax3.set_xlim(0, x_limit)
        
        # Gráfico de população
        if self.simulation.tumor_count and max(self.simulation.tumor_count) > 0:
            max_tumor = max(self.simulation.tumor_count)
            min_tumor = min([c for c in self.simulation.tumor_count if c > 0] or [1])
            self.ax2.set_ylim(max(min_tumor/2, 1), max_tumor*2)
        
        # Gráfico de crescimento
        if growth_rates:
            min_rate = min(growth_rates)
            max_rate = max(growth_rates)
            margin = abs(max_rate - min_rate) * 0.1 if max_rate != min_rate else 0.1
            self.ax3.set_ylim(min_rate - margin, max_rate + margin)
    
    def _on_close(self, event):
        """Salva resultados ao fechar."""
        print("Fechando aplicação e salvando dados...")
        
        # Parar animação
        if self.ani:
            self.ani.event_source.stop()
        
        # Salvar dados se há dados para salvar
        if self.simulation.steps:
            try:
                from data_manager import DataManager
                data_manager = DataManager()
                data_manager.save_results(self.simulation)
            except Exception as e:
                print(f"Erro ao salvar dados: {e}")
    
    def run(self):
        """Executa a visualização."""
        print("Iniciando visualização...")
        self._update_title()
        plt.tight_layout(rect=(0, 0.25, 1, 0.95))
        plt.show()