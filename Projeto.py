import flet as ft
import multiprocessing
import time
import requests
from datetime import datetime
import pandas as pd
import threading
import psutil
import platform

# Função para a aba do relógio
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

# Função para obter as cotações de moedas
def get_coin():
    quotation = requests.get("https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL,BTC-BRL")
    return quotation.json()

def process_coin(queue, lock):
    df_coin = pd.DataFrame(columns=['time', 'dollar', 'euro'])
    time.sleep(5)

    for _ in range(10):
        quotation = get_coin()
        current_time = datetime.now().strftime('%H:%M:%S')
        new_row = {
            "time": current_time,
            "dollar": f"${quotation['USDBRL']['bid']}" if quotation else "Error",
            "euro": f"${quotation['EURBRL']['bid']}" if quotation else "Error"
        }
        df_coin = pd.concat([df_coin, pd.DataFrame([new_row])], ignore_index=True)
        with lock:  # Protege o acesso à fila
            queue.put(df_coin)
        time.sleep(10)

def get_cripto():
    url = 'https://api.coingecko.com/api/v3/simple/price'
    params = {'ids': 'bitcoin,ethereum,litecoin', 'vs_currencies': 'usd'}
    quotation = requests.get(url, params=params)
    return quotation.json()

def process_cripto(queue, lock):
    df_cripto = pd.DataFrame(columns=['time', 'bitcoin', 'ethereum', 'litecoin'])

    for _ in range(10):
        quotation = get_cripto()
        current_time = datetime.now().strftime('%H:%M:%S')
        new_row = {
            "time": current_time,
            "bitcoin": f"${quotation['bitcoin']['usd']:.2f}" if quotation else "Error",
            "ethereum": f"${quotation['ethereum']['usd']:.2f}" if quotation else "Error",
            "litecoin": f"${quotation['litecoin']['usd']:.2f}" if quotation else "Error"
        }
        df_cripto = pd.concat([df_cripto, pd.DataFrame([new_row])], ignore_index=True)
        with lock:  # Protege o acesso à fila
            queue.put(df_cripto)
        time.sleep(10)

def coins_tab(page: ft.Page, queue_coin, queue_cripto):
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

# Função para mostrar o status dos processos e uso de memória
def process_status_tab(page: ft.Page, coin_process, cripto_process):
    status_text = ft.Text(value="Aguardando...", size=20)

    def update_process_status():
        try:
            coin_proc = psutil.Process(coin_process.pid)
            cripto_proc = psutil.Process(cripto_process.pid)

            # Inicialize o uso de CPU com um intervalo
            coin_proc.cpu_percent(interval=0.1)
            cripto_proc.cpu_percent(interval=0.1)
        except psutil.NoSuchProcess:
            status_text.value = "Erro ao acessar processos"
            page.update()
            return

        while coin_process.is_alive() or cripto_process.is_alive():
            try:
                # Obter uso de memória
                mem_coin = coin_proc.memory_info().rss / (1024 * 1024)
                mem_cripto = cripto_proc.memory_info().rss / (1024 * 1024)

                # Obter uso de CPU sem intervalo
                cpu_coin = coin_proc.cpu_percent()
                cpu_cripto = cripto_proc.cpu_percent()

                # Construir status
                status = (
                    f"Processo Coin:\n"
                    f"  Memória: {mem_coin:.2f} MB\n"
                    f"  CPU: {cpu_coin:.2f}%\n\n"
                    f"Processo Cripto:\n"
                    f"  Memória: {mem_cripto:.2f} MB\n"
                    f"  CPU: {cpu_cripto:.2f}%"
                )
            except psutil.NoSuchProcess:
                status = "Erro ao acessar processos"

            status_text.value = status
            page.update()
            time.sleep(1)

    status_thread = threading.Thread(target=update_process_status, daemon=True)
    status_thread.start()

    return ft.Container(content=status_text, alignment=ft.alignment.center, expand=True)



# Função de encerramento seguro
def terminate_processes(coin_process, cripto_process):
    coin_process.terminate()
    cripto_process.terminate()
    coin_process.join()
    cripto_process.join()

def system_info_tab(page: ft.Page):
    info_text = ft.Text(value="Carregando informações do sistema...", size=20)

    def fetch_system_info():
        # Informações do sistema
        os_info = f"{platform.system()} {platform.release()} ({platform.version()})"

        # CPUs e memoria
        cpu_count = psutil.cpu_count(logical=True)
        mem_info = psutil.virtual_memory()
        total_memory = mem_info.total / (1024**3)  # Convert to GB
        available_memory = mem_info.available / (1024**3)


        system_info = (
            f"Sistema Operacional: {os_info}\n"
            f"Número de CPUs: {cpu_count}\n"
            f"Memória Total: {total_memory:.2f} GB\n"
            f"Memória Disponível: {available_memory:.2f} GB\n\n"
        )

        info_text.value = system_info
        page.update()

    # Carrega as informações do sistema em uma thread separada
    threading.Thread(target=fetch_system_info, daemon=True).start()

    return ft.Container(content=info_text, alignment=ft.alignment.center, expand=True)

def main(page: ft.Page):
    page.title = "Relógio e Cotações"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.padding = 20

    queue_coin = multiprocessing.Queue()
    queue_cripto = multiprocessing.Queue()
    lock = multiprocessing.Lock()  # Cria o Lock

    coin_process = multiprocessing.Process(target=process_coin, args=(queue_coin, lock))
    cripto_process = multiprocessing.Process(target=process_cripto, args=(queue_cripto, lock))
    coin_process.start()
    cripto_process.start()

    tabs = ft.Tabs(
        tabs=[
            ft.Tab(text="Relógio", content=clock_tab(page)),
            ft.Tab(text="Moedas", content=coins_tab(page, queue_coin, queue_cripto)),
            ft.Tab(text="Status", content=process_status_tab(page, coin_process, cripto_process)),
            ft.Tab(text="Informações do Sistema", content=system_info_tab(page))
        ],
        expand=True
    )

    page.add(tabs)

    page.on_close = lambda: terminate_processes(coin_process, cripto_process)

if __name__ == "__main__":
    ft.app(target=main)
