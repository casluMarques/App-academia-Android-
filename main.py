import os
import sys
import gspread
import threading
from google.oauth2.service_account import Credentials
from datetime import datetime

from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.metrics import dp

# Imports de UI do KivyMD
from kivymd.app import MDApp
from kivymd.uix.list import ThreeLineIconListItem, IconLeftWidget
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel

# ==========================================
# 1. GERENCIAMENTO DE CAMINHOS
# ==========================================
# Verifica se está rodando empacotado no Android (MEIPASS) ou no PC
if hasattr(sys, '_MEIPASS'):
    caminho_base = sys._MEIPASS
else:
    caminho_base = os.path.dirname(os.path.abspath(__file__))

caminho_json = os.path.join(caminho_base, 'credentials.json')
caminho_kv = os.path.join(caminho_base, 'academia.kv')

# ==========================================
# 2. CONEXÃO COM A API DO GOOGLE SHEETS
# ==========================================
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
credentials = Credentials.from_service_account_file(caminho_json, scopes=SCOPES)
client = gspread.authorize(credentials)

NOME_PLANILHA = 'Planilha Treino Kivy'


# ==========================================
# 3. LÓGICA DAS TELAS
# ==========================================

class MenuScreen(Screen):
    """Tela inicial de seleção do treino."""
    pass


class TreinoScreen(Screen):
    """Tela que exibe a lista de exercícios do treino escolhido."""
    dialog_opcoes = None
    dialog_carga = None

    def carregar_exercicios(self, nome_aba, dados):
        """Lê os dados da memória e constrói a lista visual de exercícios."""
        self.nome_aba_atual = nome_aba
        self.ids.toolbar_treino.title = f"Treino {nome_aba}"
        lista = self.ids.lista_exercicios
        lista.clear_widgets() # Limpa a lista antes de popular novamente
        
        if not dados:
            lista.add_widget(MDLabel(text="Nenhum dado encontrado.", halign="center"))
            return
            
        for exercicio in dados:
            # Limpa espaços em branco nas chaves do dicionário para evitar erros de digitação na planilha
            exerc_limpo = {str(k).strip(): v for k, v in exercicio.items()}
            
            nome = exerc_limpo.get('Exercício', '')
            series = str(exerc_limpo.get('Séries', ''))
            reps = str(exerc_limpo.get('Repetições', ''))
            carga = str(exerc_limpo.get('Carga', ''))
            data_str = str(exerc_limpo.get('Última atualização de carga', ''))
            
            # Puxa o histórico das 3 últimas séries (Progressive Overload)
            rep1 = str(exerc_limpo.get('Rep 1', ''))
            rep2 = str(exerc_limpo.get('Rep 2', ''))
            rep3 = str(exerc_limpo.get('Rep 3', ''))
            historico = [rep1, rep2, rep3]
            
            # Calcula quantos dias se passaram desde o último aumento de carga
            dias_passados = "?"
            if data_str:
                try:
                    data_obj = datetime.strptime(data_str, "%d/%m/%Y")
                    dias = (datetime.now() - data_obj).days
                    dias_passados = str(dias)
                except ValueError:
                    pass
            
            # Constrói o item da lista visual
            item = ThreeLineIconListItem(
                text=f"[b]{nome}[/b]",
                secondary_text=f"{series}x {reps}  |  Carga: {carga}kg",
                tertiary_text=f"Sem subir carga há: {dias_passados} dias",
                # Passa todas as variáveis para a função mostrar_opcoes ao ser clicado
                on_release=lambda x, n=nome, s=series, r=reps, c=carga, d=dias_passados, h=historico: self.mostrar_opcoes(n, s, r, c, d, h)
            )
            # Adiciona um ícone de peso à esquerda do texto
            item.add_widget(IconLeftWidget(icon="dumbbell"))
            lista.add_widget(item)

    def mostrar_opcoes(self, nome, series, reps, carga, dias, historico):
        """Abre o pop-up inferior perguntando se o usuário quer iniciar ou mudar carga."""
        self.dialog_opcoes = MDDialog(
            title=f"Exercício: {nome}",
            text="O que você deseja fazer?",
            buttons=[
                MDFlatButton(
                    text="MUDAR CARGA",
                    theme_text_color="Custom",
                    text_color=MDApp.get_running_app().theme_cls.accent_color,
                    on_release=lambda x: self.abrir_popup_carga(nome, carga)
                ),
                MDRaisedButton(
                    text="INICIAR",
                    on_release=lambda x: self.ir_para_exercicio(nome, series, reps, carga, dias, historico)
                ),
            ],
        )
        self.dialog_opcoes.open()

    def ir_para_exercicio(self, nome, series, reps, carga, dias, historico):
        """Navega para a tela de execução e envia os parâmetros para ela."""
        if self.dialog_opcoes: self.dialog_opcoes.dismiss()
        app = MDApp.get_running_app()
        app.root.current = 'exercicio'
        tela_ex = app.root.get_screen('exercicio')
        tela_ex.montar_tela(nome, series, reps, carga, dias, historico)

    def abrir_popup_carga(self, nome, carga_atual):
        """Abre pop-up com campo de texto para digitar o novo peso."""
        if self.dialog_opcoes: self.dialog_opcoes.dismiss()
        
        self.input_nova_carga = MDTextField(
            hint_text="Nova carga (kg)",
            text=carga_atual,
            input_filter='float',
            mode="fill"
        )
        
        self.dialog_carga = MDDialog(
            title=f"Alterar: {nome}",
            type="custom",
            content_cls=self.input_nova_carga,
            buttons=[
                MDFlatButton(text="CANCELAR", on_release=lambda x: self.dialog_carga.dismiss()),
                MDRaisedButton(text="SALVAR", on_release=lambda x: self.salvar_carga(nome, self.input_nova_carga.text)),
            ],
        )
        self.dialog_carga.open()

    def salvar_carga(self, nome, nova_carga):
        """Atualiza a carga na memória local e aciona a Thread para salvar na nuvem."""
        if not nova_carga: return
        self.dialog_carga.dismiss()

        app = MDApp.get_running_app()
        aba_atual = self.nome_aba_atual
        dados_aba = app.dados_treino[aba_atual]
        hoje_str = datetime.now().strftime("%d/%m/%Y")

        # Atualiza o dicionário local para a tela refletir na mesma hora
        for exercicio in dados_aba:
            if exercicio.get('Exercício', '').strip() == nome:
                exercicio['Carga'] = nova_carga
                exercicio['Última atualização de carga'] = hoje_str
                break

        self.carregar_exercicios(aba_atual, dados_aba)
        
        # Salva no Google Sheets em segundo plano (evita travamento do app)
        threading.Thread(target=self.atualizar_planilha_bg, args=(aba_atual, nome, nova_carga, hoje_str)).start()

    def atualizar_planilha_bg(self, nome_aba, nome_exercicio, nova_carga, nova_data):
        """Função em Thread que escreve a nova carga no Google Sheets."""
        try:
            planilha = client.open(NOME_PLANILHA)
            aba = planilha.worksheet(nome_aba)
            cell = aba.find(nome_exercicio)
            if cell:
                headers = aba.row_values(1)
                col_carga = headers.index('Carga') + 1
                col_data = headers.index('Última atualização de carga') + 1
                aba.update_cell(cell.row, col_carga, nova_carga)
                aba.update_cell(cell.row, col_data, nova_data)
                print(f"[Sucesso] Carga de '{nome_exercicio}' atualizada no Sheets!")
        except Exception as e:
            print(f"[Erro] Falha ao atualizar planilha: {e}")


class ExercicioScreen(Screen):
    """Tela onde o usuário digita as repetições feitas durante o exercício."""
    dialog_resultado = None

    def montar_tela(self, nome, series, reps, carga, dias, historico):
        """Gera os campos de texto (inputs) dinamicamente dependendo do número de séries."""
        self.nome_exercicio_atual = nome
        self.meta_reps_texto = reps
        
        # Preenche as Labels do MDCard superior
        self.ids.toolbar_exercicio.title = nome
        self.ids.info_meta.text = f"Meta: {series}x {reps}"
        self.ids.info_carga.text = f"Carga Atual: {carga}kg"
        
        area = self.ids.area_series
        area.clear_widgets()
        self.inputs_series = []
        
        # Converte a série para int. Se a planilha estiver vazia, assume 1 série.
        try: num_series = int(series)
        except: num_series = 1
            
        for i in range(num_series):
            # Layout horizontal para cada série (Label + Input)
            box = MDBoxLayout(size_hint_y=None, height="60dp", spacing="15dp")
            lbl = MDLabel(text=f"Série {i+1}:", size_hint_x=0.3, halign="right", font_style="Subtitle1")
            
            # Puxa o que foi feito no treino anterior
            rep_antiga = historico[i] if i < len(historico) and historico[i] else "0"
            
            inp = MDTextField(
                hint_text=f"Última: {rep_antiga}", 
                input_filter='int', 
                mode="fill", # Design em preenchimento fica melhor no dark mode
                size_hint_x=0.7
            )
            
            box.add_widget(lbl)
            box.add_widget(inp)
            area.add_widget(box)
            self.inputs_series.append(inp)

    def verificar_resultado(self):
        """Avalia se a meta máxima foi atingida em todas as séries e aciona salvamento."""
        try:
            # Lida com metas no formato "8-12" (pega o 12)
            if '-' in self.meta_reps_texto: meta_maxima = int(self.meta_reps_texto.split('-')[1])
            else: meta_maxima = int(self.meta_reps_texto)
        except:
            meta_maxima = 0
            
        todas_atingidas = True
        novas_reps = []
        
        # Verifica input por input
        for inp in self.inputs_series:
            texto_digitado = inp.text
            novas_reps.append(texto_digitado if texto_digitado else "0")
            
            if not texto_digitado or int(texto_digitado) < meta_maxima:
                todas_atingidas = False
                
        # Inicia o salvamento das repetições na nuvem silenciosamente
        app = MDApp.get_running_app()
        aba_atual = app.root.get_screen('treino').nome_aba_atual
        threading.Thread(target=self.salvar_historico_bg, args=(aba_atual, self.nome_exercicio_atual, novas_reps)).start()
                
        # Gera o feedback pro usuário
        if todas_atingidas:
            texto_final = "Você atingiu a meta máxima em TODAS as séries!\n\nRecomendação: AUMENTE A CARGA no próximo treino."
            titulo = "Parabéns! 💪"
        else:
            texto_final = "Bom treino! Continue trabalhando com essa carga até atingir o limite de repetições em todas as séries."
            titulo = "Treino Registrado"
            
        self.dialog_resultado = MDDialog(
            title=titulo,
            text=texto_final,
            buttons=[MDFlatButton(text="OK", on_release=lambda x: self.fechar_resultado())]
        )
        self.dialog_resultado.open()

    def salvar_historico_bg(self, nome_aba, nome_exercicio, novas_reps):
        """Thread que atualiza as colunas 'Rep 1', 'Rep 2', 'Rep 3' no Google Sheets."""
        try:
            planilha = client.open(NOME_PLANILHA)
            aba = planilha.worksheet(nome_aba)
            cell = aba.find(nome_exercicio)
            
            if cell:
                headers = aba.row_values(1)
                for i, rep in enumerate(novas_reps):
                    if i < 3: # Limita a salvar apenas as 3 primeiras séries
                        nome_col = f'Rep {i+1}'
                        if nome_col in headers:
                            col_idx = headers.index(nome_col) + 1
                            aba.update_cell(cell.row, col_idx, rep)
                print(f"[Sucesso] Histórico de reps de '{nome_exercicio}' salvo!")
        except Exception as e:
            print(f"[Erro] Falha ao atualizar histórico: {e}")

    def fechar_resultado(self):
        """Fecha o popup e retorna pra lista de treino."""
        self.dialog_resultado.dismiss()
        app = MDApp.get_running_app()
        app.voltar_para('treino')

# ==========================================
# 4. INICIALIZAÇÃO DO APLICATIVO
# ==========================================
class AppTreino(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Dicionário que armazena a planilha localmente para carregamento rápido
        self.dados_treino = {'Superior': [], 'Inferior': []}

    def build(self):
        """Define o visual e carrega o arquivo KV."""
        self.theme_cls.theme_style = "Dark" 
        self.theme_cls.primary_palette = "Teal" # Verde-azulado esportivo e moderno
        self.theme_cls.primary_hue = "500"
        self.theme_cls.accent_palette = "Amber"
        
        return Builder.load_file(caminho_kv)
        
    def on_start(self):
        """Ação executada ao abrir o app: Baixa os dados da nuvem."""
        print("Baixando dados do Google Sheets...")
        try:
            planilha = client.open(NOME_PLANILHA)
            self.dados_treino['Superior'] = planilha.worksheet('Superior').get_all_records()
            self.dados_treino['Inferior'] = planilha.worksheet('Inferior').get_all_records()
            print("Dados carregados! Aplicativo pronto.")
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")

    def abrir_treino(self, nome_aba):
        """Navega da tela de Menu para a tela de Treino."""
        self.root.current = 'treino'
        tela_treino = self.root.get_screen('treino')
        tela_treino.carregar_exercicios(nome_aba, self.dados_treino[nome_aba])

    def voltar_para(self, nome_tela):
        """Função global auxiliar para os botões de retorno (setas superiores)."""
        self.root.current = nome_tela

if __name__ == '__main__':
    AppTreino().run()