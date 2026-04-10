# 🏋️‍♂️ Treinão - Workout Tracker

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Kivy](https://img.shields.io/badge/Kivy-2.3.1-green?logo=android&logoColor=white)
![Google Sheets](https://img.shields.io/badge/Google_Sheets_API-Cloud-1DA462?logo=google-sheets&logoColor=white)
![Buildozer](https://img.shields.io/badge/Buildozer-Android_APK-orange)

Aplicativo mobile de código aberto desenvolvido em **Python (Kivy/KivyMD)** focado em hipertrofia e **Progressive Overload** (Sobrecarga Progressiva). O sistema substitui os tradicionais cadernos de academia sincronizando todo o histórico de treinos, séries e cargas diretamente e em tempo real com o **Google Sheets**.

---

## ✨ Funcionalidades

* **Sincronização em Tempo Real:** Leitura e gravação de dados diretamente em uma planilha do Google Sheets via API.
* **Progressive Overload:** Exibição inteligente do histórico das últimas repetições executadas (Rep 1, Rep 2, Rep 3) durante o treino atual, forçando a progressão contínua.
* **Gestão de Cargas:** Atualização rápida do peso dos halteres/máquinas com cálculo de dias desde o último aumento de carga.
* **Interface Material Design:** UI moderna e fluida utilizando `KivyMD`, com suporte nativo a Dark Mode e componentes responsivos.
* **Processamento Assíncrono:** Operações de rede (I/O) gerenciadas em *threads* separadas (`threading`) para garantir que a interface gráfica (GUI) nunca congele durante as requisições HTTPS.

---

## 📸 Screenshots

<div align="center">
  <img src="link_da_imagem_menu.jpg" width="250px" alt="Tela de Menu" />
  <img src="link_da_imagem_lista.jpg" width="250px" alt="Lista de Exercícios" />
  <img src="link_da_imagem_exercicio.jpg" width="250px" alt="Tela de Execução" />
</div>

---

## 🛠️ Tecnologias e Bibliotecas

A arquitetura do projeto foi pensada para rodar de forma nativa no Android utilizando a infraestrutura do `python-for-android`.

* **Frontend:** [Kivy](https://kivy.org/) & [KivyMD](https://kivymd.readthedocs.io/)
* **Integração Cloud:** `gspread` e `google-auth` (OAuth2.0 via Service Account)
* **Compilação Mobile:** [Buildozer](https://buildozer.readthedocs.io/en/latest/) (Linux environment)
* **Segurança & Criptografia Embutida:** `cryptography`, `requests-oauthlib`, `pyasn1`, `openssl` (necessários para validação de tokens JWT no Android).

---

## 🚀 Como Executar o Projeto

### 1. Pré-requisitos
Você precisará de um ambiente Linux (ou WSL no Windows) para compilar o aplicativo para Android, além do Python 3 instalado.

```bash
# Clone o repositório
git clone [https://github.com/seu-usuario/treinao.git](https://github.com/seu-usuario/treinao.git)
cd treinao

# Instale as dependências locais (para testes no PC)
pip install kivy kivymd gspread google-auth
```

### 2. Configurando a API do Google
Este aplicativo requer uma **Service Account** do Google Cloud com acesso à API do Google Sheets e Google Drive.

1. Crie um projeto no [Google Cloud Console](https://console.cloud.google.com/).
2. Ative as APIs: `Google Sheets API` e `Google Drive API`.
3. Crie uma "Conta de Serviço" e gere uma chave no formato JSON.
4. Renomeie o arquivo baixado para `credentials.json` e coloque na pasta raiz do projeto.
5. Compartilhe a sua planilha com o e-mail da conta de serviço gerada.

### 3. Compilando o APK (Android)
Com o Buildozer configurado no seu ambiente Linux, execute:

```bash
# Limpa builds anteriores (recomendado ao alterar bibliotecas C/C++)
buildozer android clean

# Compila e gera o APK em modo debug
buildozer -v android debug
```
O arquivo final `.apk` estará disponível na pasta `bin/`.

---

## 🏗️ Estrutura da Planilha (Banco de Dados)

O aplicativo espera encontrar uma planilha chamada **`Planilha Treino Kivy`** com pelo menos duas abas: `Superior` e `Inferior`. As colunas obrigatórias são:

| Exercício | Séries | Repetições | Carga | Última atualização de carga | Rep 1 | Rep 2 | Rep 3 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Supino Reto | 3 | 8-12 | 30 | 10/04/2026 | 12 | 10 | 8 |

---
