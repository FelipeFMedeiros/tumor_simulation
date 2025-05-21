# tumor_simulation_simplified.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import matplotlib.animation as animation
from matplotlib.widgets import Slider, Button
import pandas as pd

# Constantes
HEALTHY = 0
TUMOR = 1
NECROTIC = 2

# Parâmetros do modelo baseados no artigo
width = 100
height = 100
initial_radius = 5
r_init = 0.0060       # Taxa de crescimento inicial
K = 1e13              # Capacidade de suporte (do artigo)
N0 = 1e9              # População inicial (do artigo)
spontaneous_rate = 0.001
max_steps = 100
treatment_factor_init = 0.0  # Valor inicial do fator de tratamento

# Variáveis globais para controle da simulação
r = r_init
treatment_factor = treatment_factor_init
paused = False
current_step = 0
animation_running = True

# Inicialização do grid
grid = np.zeros((height, width), dtype=int)
ages = np.zeros((height, width), dtype=int)

# Listas para armazenar dados
tumor_count = []
necrotic_count = []
steps = []
growth_rates = []

# Função para calcular a densidade tumoral
def get_tumor_density(x, y, grid, radius=1):
    x_min, x_max = max(0, x-radius), min(width, x+radius+1)
    y_min, y_max = max(0, y-radius), min(height, y+radius+1)
    
    subgrid = grid[y_min:y_max, x_min:x_max]
    total_cells = (y_max - y_min) * (x_max - x_min)
    tumor_cells = np.sum(subgrid == TUMOR) + np.sum(subgrid == NECROTIC)
    
    return tumor_cells / total_cells if total_cells > 0 else 0

# Inicializar o tumor
def initialize_grid():
    global grid, ages, initial_tumor_count
    
    grid = np.zeros((height, width), dtype=int)
    ages = np.zeros((height, width), dtype=int)
    
    center_x, center_y = width // 2, height // 2
    initial_tumor_count = 0
    
    for y in range(height):
        for x in range(width):
            dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            if dist <= initial_radius:
                grid[y, x] = TUMOR
                initial_tumor_count += 1
    
    return initial_tumor_count

# Primeira inicialização
initial_tumor_count = initialize_grid()

# Calcular fator de escala para alinhar contagem de células com o modelo do artigo
scale_factor = N0 / initial_tumor_count if initial_tumor_count > 0 else 1

# Configuração da visualização
fig = plt.figure(figsize=(14, 8))
plt.subplots_adjust(left=0.05, bottom=0.2, right=0.95, top=0.9, wspace=0.3)

# Layout com 3 gráficos
ax1 = plt.subplot2grid((2, 2), (0, 0), rowspan=2, colspan=1)  # Grid do tumor
ax2 = plt.subplot2grid((2, 2), (0, 1), rowspan=1, colspan=1)  # Gráfico de população
ax3 = plt.subplot2grid((2, 2), (1, 1), rowspan=1, colspan=1)  # Taxas de crescimento

# Configuração do grid visual
cmap = ListedColormap(['white', 'red', 'black'])  # Healthy, Tumor, Necrotic
im = ax1.imshow(grid, cmap=cmap, vmin=0, vmax=2)
ax1.set_title('Simulação do Crescimento Tumoral')
ax1.set_xticks([])
ax1.set_yticks([])

# Configuração inicial dos gráficos
line_tumor, = ax2.plot([], [], 'r-', linewidth=2, label='Células Tumorais')
line_necrotic, = ax2.plot([], [], 'k-', linewidth=2, label='Células Necróticas')
ax2.set_xlabel('Passos de Tempo')
ax2.set_ylabel('Contagem de Células (escala log)')
ax2.set_title('População Celular ao Longo do Tempo')
ax2.set_yscale('log')
ax2.grid(True)
ax2.legend()

line_growth, = ax3.plot([], [], 'g-', linewidth=2)
ax3.set_xlabel('Passos de Tempo')
ax3.set_ylabel('Taxa de Crescimento')
ax3.set_title('Taxa de Crescimento Instantânea')
ax3.grid(True)

# Status da simulação
status_text = plt.figtext(0.5, 0.02, "Simulação em andamento...", ha="center", fontsize=10, 
                          bbox=dict(facecolor='lightgrey', alpha=0.5))

# Adicionar sliders para controle interativo
ax_treatment = plt.axes([0.25, 0.12, 0.5, 0.03], facecolor='lightgoldenrodyellow') # type: ignore
treatment_slider = Slider(
    ax=ax_treatment,
    label='Fator de Tratamento',
    valmin=0.0,
    valmax=1.0,
    valinit=treatment_factor_init,
    color='green'
)

ax_r = plt.axes([0.25, 0.07, 0.5, 0.03], facecolor='lightgoldenrodyellow') # type: ignore
r_slider = Slider(
    ax=ax_r,
    label='Taxa de Crescimento (r)',
    valmin=0.001,
    valmax=0.02,
    valinit=r_init,
    color='blue'
)

# Botões para controle da simulação
ax_reset = plt.axes([0.8, 0.07, 0.15, 0.03]) # type: ignore
reset_button = Button(ax_reset, 'Reiniciar Simulação', color='0.9', hovercolor='0.7')

ax_pause = plt.axes([0.8, 0.12, 0.15, 0.03]) # type: ignore
pause_button = Button(ax_pause, 'Pausar', color='0.9', hovercolor='0.7')

# Funções para atualizar parâmetros
def update_r(val):
    global r
    r = val
    update_title()

def update_treatment(val):
    global treatment_factor
    treatment_factor = val
    update_title()

def update_title():
    plt.suptitle(f'Simulação do Modelo de Gompertz - r={r:.4f}, Tratamento={treatment_factor:.2f}', fontsize=14)

# Conectar sliders aos callbacks
r_slider.on_changed(update_r)
treatment_slider.on_changed(update_treatment)

# Função para pausar/continuar a simulação
def toggle_pause(event):
    global paused, animation_running
    
    # Se animação terminou, reinicia
    if not animation_running:
        restart_animation()
        status_text.set_text("Simulação reiniciada!")
        pause_button.label.set_text('Pausar')
        return
    
    # Caso contrário, pausa/continua normalmente
    paused = not paused
    status = "Pausado" if paused else "Em andamento..."
    pause_button.label.set_text('Continuar' if paused else 'Pausar')
    status_text.set_text(f"Simulação {status}")
    plt.draw()

pause_button.on_clicked(toggle_pause)

# Função para reiniciar a simulação
def reset_simulation(event):
    global grid, ages, tumor_count, necrotic_count, steps, growth_rates
    global r, treatment_factor, current_step, paused, animation_running
    
    # Reiniciar grid e dados
    initialize_grid()
    tumor_count = []
    necrotic_count = []
    steps = []
    growth_rates = []
    current_step = 0
    
    # Reiniciar parâmetros
    r = r_init
    treatment_factor = treatment_factor_init
    r_slider.set_val(r_init)
    treatment_slider.set_val(treatment_factor_init)
    
    # Reiniciar status
    paused = False
    animation_running = True
    
    # Limpar gráficos
    line_tumor.set_data([], [])
    line_necrotic.set_data([], [])
    line_growth.set_data([], [])
    
    # Atualizar visualização
    im.set_array(grid)
    update_title()
    status_text.set_text("Simulação reiniciada!")
    pause_button.label.set_text('Pausar')
    
    # Reiniciar animação
    restart_animation()

# Função para reiniciar a animação
def restart_animation():
    global ani, animation_running
    
    # Parar animação atual se existir
    try:
        ani.event_source.stop()
    except:
        pass
    
    # Criar nova animação
    ani = animation.FuncAnimation(
        fig, update, frames=range(max_steps), 
        interval=100, blit=False, repeat=False
    )
    animation_running = True

# Conectar o botão de reset
reset_button.on_clicked(reset_simulation)

# Atualizar título inicial
update_title()

# Função de atualização para animação
def update(frame):
    global grid, ages, tumor_count, necrotic_count, steps, growth_rates
    global current_step, animation_running
    
    # Atualizar contador de passos
    current_step = frame
    
    # Se estiver pausado, não atualizar
    if paused:
        return im, line_tumor, line_necrotic, line_growth
    
    # Criar cópia do grid para atualizações
    new_grid = grid.copy()
    
    # Atualizar cada célula
    for y in range(height):
        for x in range(width):
            if grid[y, x] == TUMOR:
                # Envelhecer células tumorais
                ages[y, x] += 1
                
                # Verificar morte por falta de nutrientes
                if ages[y, x] > 20:  # idade arbitrária para morte
                    tumor_density = get_tumor_density(x, y, grid)
                    if np.random.random() < tumor_density/10:
                        new_grid[y, x] = NECROTIC
                        continue
                
                # Tentar replicar para vizinhos saudáveis
                neighbors = []
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < width and 0 <= ny < height and grid[ny, nx] == HEALTHY:
                            neighbors.append((nx, ny))
                
                if neighbors:
                    # Probabilidade de divisão baseada no modelo de Gompertz
                    # Aplicação do fator de tratamento
                    tumor_density = get_tumor_density(x, y, grid)
                    # Para evitar log(0), adicionamos um pequeno valor
                    p_division = r * (1 - np.log(tumor_density + 1e-10)/np.log(1.0 + 1e-10)) * (1 - treatment_factor)
                    
                    if np.random.random() < p_division:
                        nx, ny = neighbors[np.random.randint(0, len(neighbors))]
                        new_grid[ny, nx] = TUMOR
            
            elif grid[y, x] == HEALTHY:
                # Células saudáveis podem se tornar tumorais por influência
                tumor_neighbors = 0
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < width and 0 <= ny < height and grid[ny, nx] == TUMOR:
                            tumor_neighbors += 1
                
                if tumor_neighbors > 0 and np.random.random() < spontaneous_rate * (1 - treatment_factor):
                    new_grid[y, x] = TUMOR
    
    # Atualizar o grid
    grid = new_grid
    
    # Calcular estatísticas
    tumor_cells = np.sum(grid == TUMOR)
    necrotic_cells = np.sum(grid == NECROTIC)
    
    # Armazenar dados com escala para comparar com o modelo original
    tumor_count.append(tumor_cells * scale_factor)
    necrotic_count.append(necrotic_cells * scale_factor)
    steps.append(frame)
    
    # Calcular taxa de crescimento instantânea
    if len(tumor_count) > 1 and tumor_count[-2] > 0:
        growth_rate = (tumor_count[-1] - tumor_count[-2]) / tumor_count[-2]
        growth_rates.append(growth_rate)
    elif len(tumor_count) <= 1:
        growth_rates.append(0)  # Para o primeiro ponto
    
    # Atualizar visualizações
    im.set_array(grid)
    
    line_tumor.set_data(steps, tumor_count)
    line_necrotic.set_data(steps, necrotic_count)
    
    growth_steps = steps[:len(growth_rates)]  # Garantir comprimentos iguais
    line_growth.set_data(growth_steps, growth_rates)
    
    # Ajustar limites dos gráficos
    ax2.set_xlim(0, max(steps) if steps else 10)
    ax2.set_ylim(N0/10, K*1.1)
    
    if growth_rates:
        ax3.set_xlim(0, max(steps) if steps else 10)
        min_rate = min(0, min(growth_rates)-0.01)
        max_rate = max(0.1, max(growth_rates)+0.01)
        ax3.set_ylim(min_rate, max_rate)
    
    # Atualizar status quando a simulação termina
    if frame == max_steps - 1:
        animation_running = False
        status_text.set_text("Simulação concluída! Clique em 'Pausar' para reiniciar.")
        pause_button.label.set_text('Reiniciar')
    
    return im, line_tumor, line_necrotic, line_growth

# Criar animação
ani = animation.FuncAnimation(
    fig, update, frames=range(max_steps), 
    interval=100, blit=False, repeat=False
)

# Evento para salvar resultados ao fechar
def on_close(event):
    # Se tiver dados para salvar
    if steps:
        # Garantir que todas as listas tenham o mesmo comprimento
        min_len = min(len(steps), len(tumor_count), len(necrotic_count), len(growth_rates))
        
        # Criar dataframe com comprimentos iguais
        df = pd.DataFrame({
            'Step': steps[:min_len],
            'Tumor Cells': tumor_count[:min_len],
            'Necrotic Cells': necrotic_count[:min_len],
            'Growth Rate': growth_rates[:min_len]
        })
        
        # Salvar resultados
        try:
            df.to_csv('tumor_growth_results.csv', index=False)
            print("Dados salvos com sucesso!")
            
            # Salvar imagem final
            plt.figure(figsize=(8, 8))
            plt.imshow(grid, cmap=cmap)
            plt.title(f'Estado Final do Tumor (r={r:.4f}, Tratamento={treatment_factor:.2f})')
            plt.colorbar(ticks=[0, 1, 2], label='Tipo Celular')
            plt.savefig('final_tumor_state.png')
            print("Imagem final salva com sucesso!")
        except Exception as e:
            print(f"Erro ao salvar dados: {e}")

fig.canvas.mpl_connect('close_event', on_close)

# Mostrar a visualização
plt.tight_layout(rect=[0, 0.2, 1, 0.95]) # type: ignore
plt.show()