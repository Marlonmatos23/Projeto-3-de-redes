# Monitoramento de Tráfego de Rede e Verificação de Velocidade de Internet

Este projeto oferece uma aplicação multiplataforma para **monitoramento de tráfego de rede** e **análise de velocidade de internet**. A aplicação foi desenvolvida utilizando as bibliotecas `psutil` e `speedtest-cli` para medir a largura de banda em tempo real e a velocidade de download, upload e ping, além de gerar gráficos interativos com a biblioteca `matplotlib`.

A ferramenta é capaz de detectar problemas de rede, como baixa largura de banda e alta latência, e exibe os resultados por meio de gráficos detalhados para facilitar a análise e a tomada de decisões.

## Funcionalidades

- **Monitoramento em tempo real**: Coleta dados de tráfego de rede (dados enviados e recebidos) a cada intervalo configurável.
- **Medição de velocidade de internet**: Realiza testes de download, upload e ping utilizando a biblioteca `speedtest-cli`.
- **Visualização gráfica**: Gera gráficos interativos com o desempenho da rede ao longo do tempo, utilizando a biblioteca `matplotlib`.
- **Alertas de baixa velocidade**: Emite alertas quando a velocidade de download ou upload é inferior aos valores críticos definidos (ex.: 5 Mbps para download, 1 Mbps para upload).

## Requisitos

- Python 3.x
- Bibliotecas Python:
  - `psutil`
  - `speedtest-cli`
  - `matplotlib`

## Instalação

### 1. Clone o repositório:

```bash
git clone git@github.com:Marlonmatos23/Projeto-3-de-redes.git
cd nome-do-repositorio
