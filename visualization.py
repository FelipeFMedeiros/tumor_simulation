"""Interface gráfica e visualização da simulação."""
import matplotlib.pyplot as plt
from fontTools.ttLib.woff2 import bboxFormat
from matplotlib.colors import ListedColormap
import matplotlib.animation as animation
from matplotlib.lines import lineStyles
from matplotlib.widgets import Slider, Button
import numpy as np
from mpl_toolkits.mplot3d.proj3d import transform
from pandas import interval_range

import config
from models import TumorGrid
from config import *
from models import TumorSimulation


class TumorVisualizer:
    """Classe para visualização da simulação tumoral."""
    
    def __init__(self):
        self.simulation = TumorSimulation()
        self.grid = TumorGrid()
        self.simulation.reset()
        
        self.is_running = False
        self.current_frame = 0
        self.ani = None
        
        self._setup_figure()
        self._setup_plots()
        self._setup_controls()
        self._connect_events()

        # variável de estado
        self.treatment_active = False # se não funcionar, 0 (muda pra)

    def _setup_figure(self):
        """Configura a figura principal."""
        self.fig = plt.figure(figsize=FIGURE_SIZE)
        plt.subplots_adjust(left=0.05, bottom=0.25, right=0.95, top=0.9, wspace=0.3)
        
        # Layout com 3 gráficos
        self.ax1 = plt.subplot2grid((2, 2), (0, 0), rowspan=2, colspan=1)  # Grid
        self.ax2 = plt.subplot2grid((3, 2), (0, 1), rowspan=2, colspan=1)  # População

    
    def _setup_plots(self):
        """Configura os gráficos."""
        # Grid do tumor
        self.cmap = ListedColormap(COLORS)
        self.im = self.ax1.imshow(self.simulation.tumor_grid.grid, cmap=self.cmap, vmin=0, vmax=2)
        self.ax1.set_title('Crescimento Tumoral')
        self.ax1.set_xticks([])
        self.ax1.set_yticks([])
        
        # Gráfico de população
        self.line_tumor, = self.ax2.plot([], [], 'r-', linewidth=2, label='Células Tumorais')
        self.line_necrotic, = self.ax2.plot([], [], 'k-', linewidth=2, label='Células Necróticas')
        self.ax2.set_xlabel('Ciclos de evolução tumoral, t', fontsize=10)
        self.ax2.set_ylabel('População Tumoral', fontsize=10)
        self.ax2.set_title('População Celular ao Longo do Tempo', ha='center', fontsize=12)
        self.ax2.set_yscale('log')

        #tumor_count = (np.sum(self.simulation.tumor_grid.grid == TUMOR)) *self.simulation.tumor_grid.scale_factor
        #necrotic_count = (np.sum(self.simulation.tumor_grid.grid == NECROTIC)) *self.simulation.tumor_grid.scale_factor
        #total_real = (tumor_count + necrotic_count) * self.simulation.tumor_grid.scale_factor

        #self.real_counts = initial_cells
        '''OLHAR'''

        # Ajusta o espaçamento para evitar sobreposição
        self.ax2.tick_params(axis='y', labelsize=8, pad=5)  # `pad` aumenta a distância entre números e eixo
        #===============================================================================================
        self.ax2.grid(True, alpha=0.4)
        self.ax2.legend(prop={'size': 8})
        self.ax2.set_xlim(0, MAX_STEPS * 2)  # Deixar espaço para simulações mais longas
        self.ax2.set_ylim(N0, K*1.1)



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

        #Contagem real de células
        '''COSNERTAR POSSÍVEL ENGANO NA ESCALA. foi mexido já'''
        initial_cells = self.simulation.tumor_grid.scale_factor
        self.stats_real_cells = plt.figtext(0.15, 0.2, f"Número real de células: {int(initial_cells):,}",
                                            ha='left', va='center', fontsize=12, bbox=dict(facecolor='lightgrey', alpha=0.5)
                                            )
        
        # Botões simplificados
        button_width = 0.15
        button_height = 0.04
        button_x = 0.05 #pos h vai de 0 a 1
        button_y = 0.07 #pos v vai de 0 a 1
        
        # Botão Play/Pause
        ax_play = plt.axes((0.35, button_y, button_width, button_height))
        self.play_button = Button(ax_play, 'INICIAR', color='lightgreen', hovercolor='green')
        
        # Botão Reset
        ax_reset = plt.axes((0.55, button_y, button_width, button_height))
        self.reset_button = Button(ax_reset, 'RESET', color='lightblue', hovercolor='blue')

        #Botão tratamento ON ou OFF=====================
        ax_treatment = plt.axes((0.70, 0.20, button_width, button_height))
        self.treatment_button = Button(
            ax=ax_treatment,
            label='Tratamento (OFF)',
            color='lightgray', hovercolor='0.9' #Cor ao passar o mouse
        )
        #=========================================

        #Slider controle de Gamma
        ax_gamma = plt.axes((0.60, 0.33, 0.35, 0.03), facecolor='lightgoldenrodyellow')
        self.gamma_slider = Slider(
            ax=ax_gamma, label='Efeito da droga', valmin= 0.001, valmax= 1.0, valinit=gamma, color='green'
        )

        #Slider controle C0
        ax_c0 = plt.axes((0.60, 0.30, 0.35, 0.03), facecolor='lightgoldenrodyellow')
        self.ax_c0 = Slider(
            ax= ax_c0, label= 'Concentração (c0)', valmin=0.001, valmax=1.0, valinit=c0, color='lightblue'
        )

        #Slider Taxa de Crescimento
        ax_r = plt.axes((0.60, 0.26, 0.35, 0.03), facecolor='lightgoldenrodyellow')
        self.r_slider = Slider(
            ax=ax_r, label='Taxa de \nCrescimento (r)',
            valmin=0.001, valmax=0.2, valinit=r, color='blue'
        )


    #Alterar estado e cor do botão ao ser pressionado===============================
    def toggle_treatment(self, event):
        self.treatment_active = not self.treatment_active #Invertendo o estado

        if self.treatment_active:
            self.simulation.treatment_factor = 1.0

            self.treatment_button.label.set_text('Tratamento(ON)')
            self.treatment_button.color='limegreen' #Verde quando ativo
        else:
            self.simulation.treatment_factor = 0.0
            self.treatment_button.label.set_text('Tratamento(OFF)')
            self.treatment_button.color = 'lightgray'  # Verde quando ativo

        print(f"Tratamento alterado para: {self.simulation.treatment_factor}")
        self.fig.canvas.draw() #Atualiza a figura
#=================================================================

    def _connect_events(self):
        """Conecta eventos aos controles."""
        self.r_slider.on_changed(self._on_parameter_change)
        self.gamma_slider.on_changed(self._on_parameter_change) #Adicionando slider de gamma
        self.ax_c0.on_changed(self._on_parameter_change) #Adicionando slider c0
        self.treatment_button.on_clicked(self.toggle_treatment) #Conecta função ao botão
        self.play_button.on_clicked(self._toggle_simulation)
        self.reset_button.on_clicked(self._reset_simulation)
        self.fig.canvas.mpl_connect('close_event', self._on_close)
    
    def _on_parameter_change(self, val):
        """Chamado quando um slider muda - reinicia a simulação."""
        # Atualizar parâmetros
        self.simulation.r = float(self.r_slider.val)
        self.simulation.gamma = float(self.gamma_slider.val)
        self.simulation.c0 = float(self.ax_c0.val)

        print(f'Valor de Gamma Atualizado: {self.simulation.gamma:.4f}')
        print(f"Parâmetros atualizados - r: {self.simulation.r:.4f}")

        # Reiniciar simulação automaticamente
        self._reset_simulation_data()
        self._update_title()

    
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

        #Botão e fator de tratamento OFF
        if self._reset_simulation:
            self.treatment_active = False
            self.simulation.treatment_factor = 0.0
            self.treatment_button.label.set_text('Tratamento(OFF)')
            self.treatment_button.color = 'lightgray'  # Verde quando ativo
        #===============================================================
        '''Atualizar interface'''
        self.play_button.label.set_text('INICIAR')
        self.status_text.set_text("Simulação reiniciada. Clique em 'Iniciar'")
        self.frame_text.set_text("Frame: 0")
        self.stats_text.set_text("Tumor: 0 | Necrótico: 0")

        '''TESTE'''
        #Atualizar a contagem real

        # Atualizar contagem real com valor inicial
        initial_cells = self.simulation.tumor_grid.scale_factor
        self.stats_real_cells.set_text(f"Número real de células: {int(initial_cells):,}")

        self.fig.canvas.draw_idle()
    
    def _reset_simulation_data(self):
        """Reseta apenas os dados da simulação."""
        # Resetar simulação
        self.simulation.reset()
        
        # Aplicar parâmetros atuais dos sliders
        self.simulation.r = float(self.r_slider.val)
        self.simulation.gamma = float(self.gamma_slider.val)
        self.simulation.c0 = float(self.ax_c0.val)

        '''VAMOS VER ISSO'''
        #self.simulation.treatment_factor = self.toggle_treatment() #se der errado, substitua para self.simulation.treatment
        
        # Limpar gráficos
        self.line_tumor.set_data([], [])
        self.line_necrotic.set_data([], [])
        
        # Atualizar grid visual
        self.im.set_array(self.simulation.tumor_grid.grid)
        
        # Resetar frame
        self.current_frame = 0

        #Atualiza a contagem real para o valor inicial
        initial_cells = self.simulation.tumor_grid.initial_tumor_count * self.simulation.tumor_grid.scale_factor
        self.stats_real_cells.set_text(f"Número real de células: {int(initial_cells):,}")

    def _update_frame(self, frame):
        """Atualiza frame da animação."""
        if not self.is_running:
            return [self.im, self.line_tumor, self.line_necrotic]
        
        self.current_frame = frame
        
        # Atualizar simulação
        self.simulation.update_step(frame)
        
        # Atualizar visualizações
        self.im.set_array(self.simulation.tumor_grid.grid)

        
        # Atualizar gráficos
        if self.simulation.steps:
            self.line_tumor.set_data(self.simulation.steps, self.simulation.tumor_count)
            self.line_necrotic.set_data(self.simulation.steps, self.simulation.necrotic_count)


        # Ajustar limites dinamicamente
        self._adjust_plot_limits()
        
        # Atualizar textos de status
        tumor_count = np.sum(self.simulation.tumor_grid.grid == TUMOR)
        necrotic_count = np.sum(self.simulation.tumor_grid.grid == NECROTIC)
        # Calcular células totais (tumor + necrótico)
        total_cells = (np.sum(self.simulation.tumor_grid.grid == TUMOR) + np.sum(self.simulation.tumor_grid.grid == NECROTIC))

        # Aplicar escala
        real_count = total_cells * self.simulation.tumor_grid.scale_factor
        display_text = (f"{int(real_count):.0f}" if real_count < 1e6
                        else f"{real_count:.2e}".replace('e+0', 'e'))

        self.frame_text.set_text(f"Frame: {frame}")
        self.stats_text.set_text(f"Tumor: {tumor_count} | Necrótico: {necrotic_count}")
        self.stats_real_cells.set_text(f'Número real de células: {display_text}')

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
        
        return [self.im, self.line_tumor, self.line_necrotic]

    '''FUNÇÃO NOVA'''
    def _update_log_ticks(self, y_min, y_max):
        """Atualiza os ticks do eixo Y para escala logarítmica."""
        # Gera ticks em potências de 10
        min_power = np.floor(np.log10(y_min))
        max_power = np.ceil(np.log10(y_max))

        # Cria ticks principais
        major_ticks = np.logspace(min_power, max_power, num=int(max_power - min_power) + 1)

        # Cria ticks menores (opcional)
        minor_ticks = []
        for i in range(int(min_power), int(max_power)):
            minor_ticks.extend(np.linspace(10 ** i, 10 ** (i + 1), 9)[1:-1])

        self.ax2.set_yticks(major_ticks)
        self.ax2.set_yticks(minor_ticks, minor=True)
        self.ax2.tick_params(axis='y', which='both', labelsize=8)

        # Mostra labels apenas para os ticks principais
        self.ax2.set_yticklabels([f"$10^{{{int(np.log10(t))}}}$" for t in major_ticks])

    def _adjust_plot_limits(self):
        """Ajusta limites dos gráficos dinamicamente para escala logarítmica."""
        if not self.simulation.steps or not self.simulation.tumor_count:
            return

        # Ajuste do eixo X
        max_step = max(self.simulation.steps)
        x_limit = max(max_step + 20, MAX_STEPS)
        self.ax2.set_xlim(0, x_limit)

        # Ajuste do eixo Y (escala logarítmica)
        current_tumor = self.simulation.tumor_count[-1]
        current_necrotic = self.simulation.necrotic_count[-1]

        # Define limites baseados nos valores atuais com margem
        y_min = max(N0, min(current_tumor, current_necrotic) / 10)  # 10% abaixo do menor valor
        y_max = max(current_tumor, current_necrotic) * 2  # Dobro do maior valor

        # Garante que y_min não seja zero (problema com log)
        y_min = max(y_min, 1)

        # Aplica os limites
        self.ax2.set_ylim(y_min, y_max)

        # Atualiza os ticks do eixo Y para escala log
        self._update_log_ticks(y_min, y_max)



    def _on_close(self, event):
        """Salva resultados ao fechar."""
        print("Fechando aplicação e salvando dados...")
        
        # Parar animação
        if self.ani:
            self.ani.event_source.stop()
        
        # Se houver dados para salvar
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