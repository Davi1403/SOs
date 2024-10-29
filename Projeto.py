import flet as ft
import multiprocessing
import time
import requests
from datetime import datetime
import pandas as pd
import threading


# Função do relógio (permanece como thread para atualização contínua da interface)
def clock_tab(page: ft.Page):
    time_display = ft.Text(value="00:00:00", size=50, weight="bold")

    def update_clock():
        while True:
            current_time = datetime.now().strftime("%H:%M:%S")
            time_display.value = current_time
            page.update()
            time.sleep(1)   

    clock_thread = threading.Thread(target=update_clock, daemon=True)
    clock_thread.start()

    return ft.Container(
        content=time_display,
        alignment=ft.alignment.center,
        expand=True
    )

# Funções para cotações de moedas
def get_coin():
    quotation = requests.get("https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL,BTC-BRL")
    return quotation.json()

def process_coin(queue):
    df_coin = pd.DataFrame(columns=['time', 'dollar', 'euro'])
    time.sleep(5)       

    for _ in range(10):  # Limita o número de atualizações
        quotation = get_coin()
        current_time = datetime.now().strftime('%H:%M:%S')

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

        df_coin = pd.concat([df_coin, pd.DataFrame([new_row])], ignore_index=True)
        queue.put(df_coin)  # Envia os dados para a fila
        time.sleep(10)

# Funções para cotações de criptomoedas
def get_cripto():
    url = 'https://api.coingecko.com/api/v3/simple/price'
    params = {'ids': 'bitcoin,ethereum,litecoin', 'vs_currencies': 'usd'}
    quotation = requests.get(url, params=params)
    return quotation.json()

def process_cripto(queue):
    df_cripto = pd.DataFrame(columns=['time', 'bitcoin', 'ethereum', 'litecoin'])

    for _ in range(10):  # Limita o número de atualizações
        quotation = get_cripto()
        current_time = datetime.now().strftime('%H:%M:%S')

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

        df_cripto = pd.concat([df_cripto, pd.DataFrame([new_row])], ignore_index=True)
        queue.put(df_cripto)  # Envia os dados para a fila
        time.sleep(10)

# Função para criar a aba de moedas e criptomoedas
def coins_tab(page: ft.Page, queue_coin, queue_cripto):
    # Criação das tabelas
    coin_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Time")),
            ft.DataColumn(ft.Text("Dollar")),
            ft.DataColumn(ft.Text("Euro"))
        ],
        rows=[]
    )

    cripto_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Time")),
            ft.DataColumn(ft.Text("Bitcoin")),
            ft.DataColumn(ft.Text("Ethereum")),
            ft.DataColumn(ft.Text("Litecoin"))
        ],
        rows=[]
    )

    def update_coin_table(df):
        coin_table.rows.clear()
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
        page.update()

    def update_cripto_table(df):
        cripto_table.rows.clear()
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
        page.update()

    # Atualiza as tabelas com base nas filas
    def monitor_queues():
        while True:
            if not queue_coin.empty():
                df_coin = queue_coin.get()
                update_coin_table(df_coin)
            if not queue_cripto.empty():
                df_cripto = queue_cripto.get()
                update_cripto_table(df_cripto)
            time.sleep(1)

    monitor_thread = threading.Thread(target=monitor_queues, daemon=True)
    monitor_thread.start()

    # Layout da página com as duas colunas
    content = ft.Row(
        [
            ft.Column(
                [
                    ft.Text("Cotações de Moedas", size=20, weight="bold"),
                    coin_table,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                width=400  # Largura da coluna
            ),
            ft.VerticalDivider(),  # Divisor entre as colunas
            ft.Column(
                [
                    ft.Text("Cotações de Criptomoedas", size=20, weight="bold"),
                    cripto_table,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                width=400  # Largura da coluna
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )

    return content

# Função principal
def main(page: ft.Page):
    page.title = "Relógio e Cotações"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.padding = 20

    # Filas para comunicação entre processos
    queue_coin = multiprocessing.Queue()
    queue_cripto = multiprocessing.Queue()

    # Iniciar processos
    coin_process = multiprocessing.Process(target=process_coin, args=(queue_coin,))
    cripto_process = multiprocessing.Process(target=process_cripto, args=(queue_cripto,))
    coin_process.start()
    cripto_process.start()

    # Definir abas
    tabs = ft.Tabs(
        tabs=[
            ft.Tab(text="Relógio", content=clock_tab(page)),
            ft.Tab(text="Moedas", content=coins_tab(page, queue_coin, queue_cripto))
        ],
        expand=True
    )

    page.add(tabs)

# Inicia o aplicativo Flet
if __name__ == "__main__":
    ft.app(target=main)
