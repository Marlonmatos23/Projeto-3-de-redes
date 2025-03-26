import psutil
import time
import matplotlib.pyplot as plt
import argparse
import sys
import logging
import speedtest

# Configuração do logging
logging.basicConfig(
    level=logging.DEBUG,  # Alterado para DEBUG para mais detalhes
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)

def send_alert(message):
    """
    Exibe uma mensagem de alerta via logging e emite um beep.
    """
    logging.warning(message)
    print('\a')  # Beep (pode não funcionar em todos os sistemas)

def get_available_interfaces():
    """
    Retorna uma lista com os nomes de todas as interfaces disponíveis.
    Excluindo a interface 'lo' (loopback) e outras não-relevantes.
    """
    interfaces = list(psutil.net_io_counters(pernic=True).keys())
    if 'lo' in interfaces:
        interfaces.remove('lo')  # Remove a interface de loopback
    return interfaces

def auto_select_interface():
    """
    Seleciona automaticamente a primeira interface de rede ativa, excluindo 'lo'.
    """
    available = get_available_interfaces()
    for interface in available:
        stats = psutil.net_io_counters(pernic=True).get(interface)
        if stats and (stats.bytes_sent > 0 or stats.bytes_recv > 0):
            logging.info(f"Interface '{interface}' está ativa.")
            return interface
    send_alert("Nenhuma interface ativa encontrada.")
    return None

def check_internet_speed():
    """
    Verifica a velocidade da internet (download e upload) e retorna os valores.
    """
    st = speedtest.Speedtest()

    try:
        # Força a seleção do melhor servidor
        st.get_best_server()

        # Faz o teste de download e upload
        download_speed = st.download() / 1_000_000  # em Mbps
        upload_speed = st.upload() / 1_000_000  # em Mbps

        # Calcula o ping
        ping = st.results.ping

        logging.info(f"Velocidade de Download: {download_speed:.2f} Mbps")
        logging.info(f"Velocidade de Upload: {upload_speed:.2f} Mbps")
        logging.info(f"Ping: {ping} ms")

        # Verifica se a velocidade está preocupante
        if download_speed < 5:  # 5 Mbps como limite para download
            send_alert("Velocidade de download preocupante! (<5 Mbps)")
        if upload_speed < 1:  # 1 Mbps como limite para upload
            send_alert("Velocidade de upload preocupante! (<1 Mbps)")

        return download_speed, upload_speed, ping

    except speedtest.ConfigRetrievalError as e:
        send_alert(f"Erro ao recuperar a configuração do servidor: {e}")
        return None, None, None

def monitor_network_traffic(interface, duration=30, interval=1, force_monitor=False):
    """
    Monitora o tráfego de rede e retorna listas de tempos e largura de banda (em Mbits/sec).
    Agora, também coleta dados específicos para protocolos TCP, UDP, ICMP.

    :param interface: Nome da interface de rede a ser monitorada.
    :param duration: Duração total do monitoramento (em segundos).
    :param interval: Intervalo entre as medições (em segundos).
    :param force_monitor: Se True, ignora a verificação do status da interface.
    :return: (time_values, bw_values, tcp_values, udp_values, icmp_values)
    """
    time_values, bw_values, tcp_values, udp_values, icmp_values = [], [], [], [], []

    if interval <= 0:
        send_alert("O intervalo deve ser maior que zero.")
        return [], [], [], [], []

    stats = psutil.net_io_counters(pernic=True)
    if interface not in stats:
        send_alert(f"Interface '{interface}' não encontrada.")
        logging.info("Interfaces disponíveis: %s", get_available_interfaces())
        return [], [], [], [], []

    # Dados iniciais
    initial_stats = stats[interface]
    initial_bytes_sent = initial_stats.bytes_sent
    initial_bytes_recv = initial_stats.bytes_recv

    start_time = time.time()
    logging.info("Monitoramento iniciado na interface '%s'.", interface)

    try:
        while (elapsed := time.time() - start_time) < duration:
            # Verifica o status da interface, a menos que forçado
            interface_stats = psutil.net_if_stats().get(interface)
            if interface_stats is None:
                send_alert(f"Não foi possível obter o status da interface '{interface}'.")
                logging.info("Interfaces disponíveis: %s", get_available_interfaces())
                break
            if not interface_stats.isup and not force_monitor:
                send_alert(f"A conexão na interface '{interface}' foi interrompida.")
                break

            time_values.append(round(elapsed, 1))

            current_stats = psutil.net_io_counters(pernic=True).get(interface)
            if current_stats is None:
                send_alert(f"Interface '{interface}' não encontrada durante a execução.")
                logging.info("Interfaces disponíveis: %s", get_available_interfaces())
                break

            current_bytes_sent = current_stats.bytes_sent
            current_bytes_recv = current_stats.bytes_recv

            # Exibe as contagens de bytes a cada intervalo para depuração
            logging.debug(f"Contadores atuais: Enviados={current_bytes_sent}, Recebidos={current_bytes_recv}")

            # Calcula a largura de banda (Mbits/sec) para envio e recebimento
            sent_bw = ((current_bytes_sent - initial_bytes_sent) * 8) / (interval * 1024 * 1024)
            recv_bw = ((current_bytes_recv - initial_bytes_recv) * 8) / (interval * 1024 * 1024)
            total_bw = sent_bw + recv_bw
            bw_values.append(total_bw)

            # Coleta dados específicos de protocolos (TCP, UDP, ICMP)
            tcp_stats = psutil.net_connections(kind='tcp')
            udp_stats = psutil.net_connections(kind='udp')
            icmp_stats = psutil.net_if_stats()  # Não diretamente, mas podemos monitorar pacotes ICMP

            tcp_values.append(len(tcp_stats))  # Contagem de conexões TCP
            udp_values.append(len(udp_stats))  # Contagem de conexões UDP
            icmp_values.append(sum(1 for _ in icmp_stats.values() if 'icmp' in _))  # Exemplo simplificado para ICMP

            # Atualiza os contadores para a próxima iteração
            initial_bytes_sent = current_bytes_sent
            initial_bytes_recv = current_bytes_recv

            logging.debug(f"Largura de banda (Mbits/sec): Enviado={sent_bw:.6f}, Recebido={recv_bw:.6f}, Total={total_bw:.6f}")
            logging.debug(f"Conexões TCP: {len(tcp_stats)}, UDP: {len(udp_stats)}, ICMP: {icmp_values[-1]}")

            time.sleep(interval)
    except KeyboardInterrupt:
        send_alert("Monitorização interrompida pelo usuário.")
    except Exception as e:
        send_alert(f"Ocorreu um erro: {e}")

    return time_values, bw_values, tcp_values, udp_values, icmp_values

def plot_network_traffic(time_values, bw_values, tcp_values, udp_values, icmp_values, save_path=None):
    """
    Gera e exibe o gráfico da largura de banda ao longo do tempo.
    Adicionando visualização para TCP, UDP e ICMP.

    :param time_values: Lista de tempos (s).
    :param bw_values: Lista de largura de banda (Mbits/sec).
    :param tcp_values: Lista de contagem de conexões TCP.
    :param udp_values: Lista de contagem de conexões UDP.
    :param icmp_values: Lista de pacotes ICMP (aproximado).
    :param save_path: Se informado, salva o gráfico no caminho especificado.
    """
    plt.figure(figsize=(10, 6))
    plt.plot(time_values, bw_values, marker='o', linestyle='-', label='Largura de Banda')
    plt.plot(time_values, tcp_values, marker='x', linestyle='--', label='Conexões TCP')
    plt.plot(time_values, udp_values, marker='^', linestyle='-.', label='Conexões UDP')
    plt.plot(time_values, icmp_values, marker='s', linestyle=':', label='Pacotes ICMP')

    # Adiciona valores no gráfico
    for x, y in zip(time_values, bw_values):
        plt.text(x, y, f"{y:.2f}", fontsize=8, ha='center')

    plt.xlabel("Tempo (s)")
    plt.ylabel("Métrica")
    plt.title("Monitoramento de Tráfego de Rede")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    if save_path:
        try:
            plt.savefig(save_path)
            logging.info("Gráfico salvo em %s", save_path)
        except Exception as e:
            send_alert(f"Erro ao salvar o gráfico: {e}")
    plt.show()

def main():
    parser = argparse.ArgumentParser(description="Monitoramento de tráfego de rede")
    parser.add_argument("-i", "--interface", type=str, help="Nome da interface de rede a ser monitorada")
    parser.add_argument("-d", "--duration", type=int, default=30, help="Duração do monitoramento (segundos)")
    parser.add_argument("-t", "--interval", type=int, default=1, help="Intervalo entre medições (segundos)")
    parser.add_argument("-s", "--save", type=str, help="Caminho para salvar o gráfico (ex: grafico.png)")
    parser.add_argument("-f", "--force", action="store_true", help="Força o monitoramento mesmo se a interface estiver inativa")
    parser.add_argument("--list", action="store_true", help="Lista todas as interfaces de rede disponíveis")

    args = parser.parse_args()

    if args.list:
        print("Interfaces disponíveis:")
        for iface in get_available_interfaces():
            print("-", iface)
        sys.exit(0)

    # Seleção automática da interface ativa
    interface = args.interface if args.interface else auto_select_interface()

    if not interface:
        send_alert("Nenhuma interface de rede ativa encontrada no sistema.")
        sys.exit(1)

    logging.info(f"Iniciando monitoramento na interface '{interface}' por {args.duration} segundos.")
    
    # Verifica a velocidade da internet
    check_internet_speed()

    time_values, bw_values, tcp_values, udp_values, icmp_values = monitor_network_traffic(
        interface=interface,
        duration=args.duration,
        interval=args.interval,
        force_monitor=args.force
    )

    if time_values and bw_values:
        plot_network_traffic(time_values, bw_values, tcp_values, udp_values, icmp_values, save_path=args.save)
    else:
        send_alert("Erro ao capturar dados de tráfego de rede.")

if __name__ == "__main__":
    main()
