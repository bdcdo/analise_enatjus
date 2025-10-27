"""
Análise de adesão temporal por instituição.

Este script analisa a evolução temporal da adesão das instituições ao E-NatJus,
gerando análises de urgência, gráficos de acumulado, média móvel e distribuição anual.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import logging
from utils import (
    carregar_base_enatjus,
    criar_pasta_outputs,
    salvar_excel,
    obter_cor,
    logger
)

# Configurar pandas
pd.set_option('display.max_columns', None)


def preparar_dados_temporais(df):
    """
    Prepara dados para análise temporal.

    Args:
        df (pd.DataFrame): DataFrame completo

    Returns:
        pd.DataFrame: DataFrame preparado com dados temporais
    """
    logger.info("Preparando dados temporais...")

    # Selecionar colunas relevantes
    colunas = ['idNotaTecnica', 'arquivo', 'origem_tratada', 'data_emissao', 'selAlegacaoUrgencia']
    df_temp = df[colunas].copy()

    # Processar data
    df_temp['data'] = pd.to_datetime(df_temp['data_emissao']).dt.date
    df_temp['ano'] = pd.to_datetime(df_temp['data_emissao']).dt.year
    df_temp['mes'] = pd.to_datetime(df_temp['data_emissao']).dt.to_period('M')

    # Ordenar por data
    df_temp = df_temp.sort_values('data')
    df_temp['contagem'] = 1

    logger.info(f"Dados temporais preparados: {len(df_temp)} registros")
    return df_temp


def analisar_urgencia_por_instituicao(df, pasta_output='outputs'):
    """
    Analisa a proporção de pareceres urgentes por instituição.

    Args:
        df (pd.DataFrame): DataFrame com dados
        pasta_output (str): Pasta para salvar resultados
    """
    logger.info("Analisando urgência por instituição...")

    resultado = []

    for inst in df['origem_tratada'].unique():
        urgencia_counts = df.loc[df['origem_tratada'] == inst]['selAlegacaoUrgencia'].value_counts(normalize=True)

        temp_df = urgencia_counts.reset_index()
        temp_df.columns = ['Nível de Urgência', 'Percentual']
        temp_df['Instituição'] = inst
        temp_df = temp_df[['Instituição', 'Nível de Urgência', 'Percentual']]

        resultado.append(temp_df)

    result_df = pd.concat(resultado, ignore_index=True)
    salvar_excel(result_df, 'analise_urgencia_instituicoes.xlsx', pasta_output)

    logger.info(f"Análise de urgência salva: {len(result_df)} registros")


def gerar_tabela_adesao_anual(df, pasta_output='outputs'):
    """
    Gera tabela com adesão anual por instituição.

    Args:
        df (pd.DataFrame): DataFrame com dados temporais
        pasta_output (str): Pasta para salvar resultados
    """
    logger.info("Gerando tabela de adesão anual...")

    # Crosstab de instituições por ano
    crossdf = pd.crosstab(df['origem_tratada'], df['ano'], margins=True, margins_name="Total")
    crossdf_reset = crossdf.reset_index()

    # Calcular total sem Nacional
    if 'Nacional' in crossdf_reset['origem_tratada'].values:
        df_nacional = crossdf_reset.loc[crossdf_reset['origem_tratada'] == 'Nacional']
        df_total = crossdf_reset.loc[crossdf_reset['origem_tratada'] == 'Total']

        if not df_nacional.empty and not df_total.empty:
            valores_sem_nacional = df_total.iloc[:, 1:-1].values - df_nacional.iloc[:, 1:-1].values
            df_total_sem_nacional = pd.DataFrame(data=valores_sem_nacional, columns=crossdf.columns[:-1])
            df_total_sem_nacional['origem_tratada'] = 'Total sem Nacional'
            crossdf_final = pd.concat([crossdf_reset, df_total_sem_nacional], ignore_index=True)
        else:
            crossdf_final = crossdf_reset
    else:
        crossdf_final = crossdf_reset

    salvar_excel(crossdf_final, 'total_adesao.xlsx', pasta_output)
    logger.info(f"Tabela de adesão anual salva: {len(crossdf_final)} instituições")


def grafico_acumulado(df, lista_inst, pasta_output='outputs', nome_arquivo='grafico_acumulado.png'):
    """
    Gera gráfico de pareceres acumulados ao longo do tempo.

    Args:
        df (pd.DataFrame): DataFrame com dados temporais
        lista_inst (list): Lista de instituições a plotar
        pasta_output (str): Pasta para salvar o gráfico
        nome_arquivo (str): Nome do arquivo de saída
    """
    logger.info(f"Gerando gráfico acumulado para {len(lista_inst)} instituições...")

    df['data'] = pd.to_datetime(df['data'])
    current_df = df.loc[df['origem_tratada'].isin(lista_inst)].copy()
    df_cumsum = current_df.groupby(['origem_tratada', 'data']).count().groupby(level=0).cumsum().reset_index()
    df_cumsum_filtrado = df_cumsum[df_cumsum['data'] <= '2024-12-31']

    plt.figure(figsize=(7, 5), dpi=500)
    for orgao in df_cumsum_filtrado['origem_tratada'].unique():
        orgao_data = df_cumsum_filtrado[df_cumsum_filtrado['origem_tratada'] == orgao]
        plt.plot(orgao_data['data'], orgao_data['contagem'], label=orgao, color=obter_cor(orgao))

    plt.legend(title='Órgãos')
    plt.grid()
    plt.ylim(bottom=0)
    plt.xlim(left=df_cumsum_filtrado['data'].min(), right=pd.to_datetime('2024-12-31'))
    plt.tight_layout()

    caminho = os.path.join(pasta_output, nome_arquivo)
    plt.savefig(caminho, bbox_inches='tight')
    plt.close()

    logger.info(f"Gráfico acumulado salvo: {caminho}")


def grafico_media_movel(df, lista_inst, pasta_output='outputs', nome_arquivo='grafico_media_movel.png'):
    """
    Gera gráfico de média móvel de 12 meses.

    Args:
        df (pd.DataFrame): DataFrame com dados temporais
        lista_inst (list): Lista de instituições a plotar
        pasta_output (str): Pasta para salvar o gráfico
        nome_arquivo (str): Nome do arquivo de saída
    """
    logger.info(f"Gerando gráfico de média móvel para {len(lista_inst)} instituições...")

    current_df = df.copy()
    current_df['origem_tratada'] = current_df['origem_tratada'].apply(lambda x: x if x in lista_inst else 'Outros')

    # Agrupar por instituição e mês
    df_monthly = current_df.groupby(['origem_tratada', 'mes']).size().reset_index(name='contagem')
    df_monthly['data'] = df_monthly['mes'].dt.to_timestamp()

    # Calcular média móvel de 12 meses
    df_monthly['media_movel'] = df_monthly.groupby('origem_tratada')['contagem'].transform(
        lambda x: x.rolling(window=12, min_periods=1).mean()
    )

    # Organizar ordem das instituições
    inst_responsaveis = df_monthly['origem_tratada'].unique().tolist()
    for orgao in ['Outros', 'Nacional']:
        if orgao in inst_responsaveis:
            inst_responsaveis.remove(orgao)
            inst_responsaveis.insert(0, orgao)

    plt.figure(figsize=(6, 4.5), dpi=3000)
    for orgao in inst_responsaveis:
        orgao_data = df_monthly[df_monthly['origem_tratada'] == orgao]
        plt.plot(orgao_data['data'], orgao_data['media_movel'], label=orgao, color=obter_cor(orgao))

    plt.legend(title='Órgãos')
    plt.grid(True)
    plt.ylim(bottom=0)
    plt.xlim(left=df_monthly['data'].min(), right=pd.to_datetime('2024-12-31'))
    plt.tight_layout()

    caminho = os.path.join(pasta_output, nome_arquivo)
    plt.savefig(caminho, bbox_inches='tight')
    plt.close()

    logger.info(f"Gráfico de média móvel salvo: {caminho}")


def grafico_stackplot(df, lista_inst, pasta_output='outputs', nome_arquivo='grafico_stackplot.png'):
    """
    Gera gráfico stackplot da distribuição anual.

    Args:
        df (pd.DataFrame): DataFrame com dados temporais
        lista_inst (list): Lista de instituições a plotar
        pasta_output (str): Pasta para salvar o gráfico
        nome_arquivo (str): Nome do arquivo de saída
    """
    logger.info(f"Gerando stackplot para {len(lista_inst)} instituições...")

    current_df = df.copy()
    current_df['origem_tratada'] = current_df['origem_tratada'].apply(lambda x: x if x in lista_inst else 'Outros')

    # Calcular contagem anual
    df_count = current_df.groupby(['origem_tratada', 'ano']).count().reset_index()

    # Preparar dados para stackplot
    pivot_df = df_count.pivot(index='ano', columns='origem_tratada', values='contagem').fillna(0)

    # Organizar colunas
    columns = list(pivot_df.columns)
    for orgao in ['Outros', 'Nacional']:
        if orgao in columns:
            columns.remove(orgao)
            columns.append(orgao)
    pivot_df = pivot_df[columns]

    plt.figure(figsize=(6, 4.5), dpi=3000)
    plt.stackplot(pivot_df.index, pivot_df.T, labels=pivot_df.columns,
                  colors=[obter_cor(orgao) for orgao in pivot_df.columns])

    plt.legend(title='Órgãos', loc='upper left')
    plt.grid()
    plt.ylim(bottom=0)
    plt.xlim(left=pivot_df.index.min(), right=2024)
    plt.tight_layout()

    caminho = os.path.join(pasta_output, nome_arquivo)
    plt.savefig(caminho, bbox_inches='tight')
    plt.close()

    logger.info(f"Stackplot salvo: {caminho}")


def main():
    """
    Função principal que executa todas as análises.
    """
    logger.info("=" * 60)
    logger.info("INICIANDO ANÁLISE DE ADESÃO")
    logger.info("=" * 60)

    # Criar pasta de outputs
    pasta_output = 'outputs'
    criar_pasta_outputs(pasta_output)

    # Carregar base de dados
    caminho_base = os.path.join('..', 'base_enatjus_2025-1.parquet')
    df = carregar_base_enatjus(caminho_base)

    # Preparar dados temporais
    df_temp = preparar_dados_temporais(df)

    # Análises
    analisar_urgencia_por_instituicao(df_temp, pasta_output)
    gerar_tabela_adesao_anual(df_temp, pasta_output)

    # Selecionar top 10 instituições para gráficos
    top_10_com_nacional = df_temp.loc[df_temp['origem_tratada'] != 'NÃO_PREENCHIDO']['origem_tratada'].value_counts().head(10).index.tolist()
    top_10_sem_nacional = df_temp.loc[(df_temp['origem_tratada'] != 'NÃO_PREENCHIDO') & (df_temp['origem_tratada'] != 'Nacional')]['origem_tratada'].value_counts().head(10).index.tolist()

    # Gerar gráficos
    grafico_acumulado(df_temp, top_10_sem_nacional, pasta_output, 'grafico_acumulado_sem_nacional.png')
    grafico_media_movel(df_temp, top_10_com_nacional, pasta_output, 'grafico_media_movel.png')
    grafico_stackplot(df_temp, top_10_com_nacional, pasta_output, 'grafico_stackplot.png')

    logger.info("=" * 60)
    logger.info("ANÁLISE DE ADESÃO CONCLUÍDA COM SUCESSO")
    logger.info(f"Resultados salvos em: {pasta_output}/")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
