import flet as ft
import multiprocessing
import time
import requests
from datetime import datetime
import pandas as pd
import threading


# Função para a aba do relógio (permanece como thread para atualização contínua da interface)
def clock_tab(page: ft.Page):
    # Cria um elemento de texto para exibir a hora atual
    time_display = ft.Text(value="00:00:00", size=50, weight="bold")

    # Função para atualizar a hora continuamente
    def update_clock():
        while True:
            current_time = datetime.now().strftime("%H:%M:%S")  # Obtém a hora atual
            time_display.value = current_time  # Atualiza o valor do texto com a hora atual
            page.update()  # Atualiza a interface da página
            time.sleep(1)  # Aguarda 1 segundo antes da próxima atualização

    # Inicia um thread para executar a função update_clock em segundo plano
    clock_thread = threading.Thread(target=update_clock, daemon=True)
    clock_thread.start()

    # Retorna o container que exibe a hora no centro da página
    return ft.Container(
        content=time_display,
        alignment=ft.alignment.center,
        expand=True
    )

# Função para obter as cotações de moedas (dólar e euro)
def get_coin():
    quotation = requests.get("https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL,BTC-BRL")
    return quotation.json()

# Função de processo para atualizar cotações de moedas periodicamente
def process_coin(queue):
    # Cria um DataFrame vazio para armazenar as cotações
    df_coin = pd.DataFrame(columns=['time', 'dollar', 'euro'])
    time.sleep(5)  # Aguarda 5 segundos antes de iniciar a primeira atualização

    # Limita o número de atualizações para 10 ciclos
    for _ in range(10):
        quotation = get_coin()  # Obtém as cotações da API
        current_time = datetime.now().strftime('%H:%M:%S')  # Obtém a hora atual

        # Adiciona uma nova linha ao DataFrame com as cotações
        if quotation:
            new_row = {
                "time": current_time,
                "dollar": f"${quotation['USDBRL']['bid']}",
                "euro": f"${quotation['EURBRL']['bid']}"
            }
        else:
            new_row = {
                "time": "Error",
                "dollar": "Error",
                "euro": "Error"
            }

        # Concatena o DataFrame com a nova linha e coloca-o na fila para a interface
        df_coin = pd.concat([df_coin, pd.DataFrame([new_row])], ignore_index=True)
        queue.put(df_coin)
        time.sleep(10)  # Aguarda 10 segundos para a próxima atualização

# Função para obter as cotações de criptomoedas (Bitcoin, Ethereum e Litecoin)
def get_cripto():
    url = 'https://api.coingecko.com/api/v3/simple/price'
    params = {'ids': 'bitcoin,ethereum,litecoin', 'vs_currencies': 'usd'}
    quotation = requests.get(url, params=params)
    return quotation.json()

# Função de processo para atualizar cotações de criptomoedas periodicamente
def process_cripto(queue):
    # Cria um DataFrame vazio para armazenar as cotações
    df_cripto = pd.DataFrame(columns=['time', 'bitcoin', 'ethereum', 'litecoin'])

    # Limita o número de atualizações para 10 ciclos
    for _ in range(10):
        quotation = get_cripto()  # Obtém as cotações da API
        current_time = datetime.now().strftime('%H:%M:%S')  # Obtém a hora atual

        # Adiciona uma nova linha ao DataFrame com as cotações
        if quotation:
            new_row = {
                "time": current_time,
                "bitcoin": f"${quotation['bitcoin']['usd']:.2f}",
                "ethereum": f"${quotation['ethereum']['usd']:.2f}",
                "litecoin": f"${quotation['litecoin']['usd']:.2f}"
            }
        else:
            new_row = {
                "time": "Error",
                "bitcoin": "Error",
                "ethereum": "Error",
                "litecoin": "Error"
            }

        # Concatena o DataFrame com a nova linha e coloca-o na fila para a interface
        df_cripto = pd.concat([df_cripto, pd.DataFrame([new_row])], ignore_index=True)
        queue.put(df_cripto)
        time.sleep(10)  # Aguarda 10 segundos para a próxima atualização

# Função para criar a aba de exibição das cotações de moedas e criptomoedas
def coins_tab(page: ft.Page, queue_coin, queue_cripto):
    # Cria uma tabela para exibir cotações de moedas
    coin_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Time")),
            ft.DataColumn(ft.Text("Dollar")),
            ft.DataColumn(ft.Text("Euro"))
        ],
        rows=[]
    )

    # Cria uma tabela para exibir cotações de criptomoedas
    cripto_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Time")),
            ft.DataColumn(ft.Text("Bitcoin")),
            ft.DataColumn(ft.Text("Ethereum")),
            ft.DataColumn(ft.Text("Litecoin"))
        ],
        rows=[]
    )

    # Função para atualizar a tabela de moedas
    def update_coin_table(df):
        coin_table.rows.clear()  # Limpa as linhas da tabela
        for _, row in df.iterrows():
            coin_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(row['time'])),
                        ft.DataCell(ft.Text(row['dollar'])),
                        ft.DataCell(ft.Text(row['euro']))
                    ]
                )
            )
        page.update()  # Atualiza a interface da página

    # Função para atualizar a tabela de criptomoedas
    def update_cripto_table(df):
        cripto_table.rows.clear()  # Limpa as linhas da tabela
        for _, row in df.iterrows():
            cripto_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(row['time'])),
                        ft.DataCell(ft.Text(row['bitcoin'])),
                        ft.DataCell(ft.Text(row['ethereum'])),
                        ft.DataCell(ft.Text(row['litecoin']))
                    ]
                )
            )
        page.update()  # Atualiza a interface da página

    # Função para monitorar as filas e atualizar as tabelas
    def monitor_queues():
        while True:
            # Verifica se há novos dados na fila de moedas
            if not queue_coin.empty():
                df_coin = queue_coin.get()
                update_coin_table(df_coin)
            # Verifica se há novos dados na fila de criptomoedas
            if not queue_cripto.empty():
                df_cripto = queue_cripto.get()
                update_cripto_table(df_cripto)
            time.sleep(1)  # Aguarda 1 segundo antes de verificar novamente

    # Inicia um thread para monitorar as filas
    monitor_thread = threading.Thread(target=monitor_queues, daemon=True)
    monitor_thread.start()

    # Layout da aba com duas colunas (moedas e criptomoedas)
    content = ft.Row(
        [
            ft.Column(
                [
                    ft.Text("Cotações de Moedas", size=20, weight="bold"),
                    coin_table,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                width=400
            ),
            ft.VerticalDivider(),
            ft.Column(
                [
                    ft.Text("Cotações de Criptomoedas", size=20, weight="bold"),
                    cripto_table,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                width=400
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )

    return content

# Função principal para configurar a página e iniciar os processos
def main(page: ft.Page):
    # Configura a página principal
    page.title = "Relógio e Cotações"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.padding = 20

    # Cria filas para comunicação entre processos
    queue_coin = multiprocessing.Queue()
    queue_cripto = multiprocessing.Queue()

    # Inicia os processos para atualizar as cotações de moedas e criptomoedas
    coin_process = multiprocessing.Process(target=process_coin, args=(queue_coin,))
    cripto_process = multiprocessing.Process(target=process_cripto, args=(queue_cripto,))
    coin_process.start()
    cripto_process.start()

    # Define as abas (Relógio e Cotações)
    tabs = ft.Tabs(
        tabs=[
            ft.Tab(text="Relógio", content=clock_tab(page)),
            ft.Tab(text="Moedas", content=coins_tab(page, queue_coin, queue_cripto))
        ],
        expand=True
    )

    # Adiciona as abas à página
    page.add(tabs)

# Inicia o aplicativo Flet
if __name__ == "__main__":
    ft.app(target=main)
