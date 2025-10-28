"""
Análise de divergências regionais nas taxas de concessão.

Este script analisa as taxas de concessão (pareceres favoráveis) por instituição,
incluindo análises gerais e por subconjuntos específicos (offlabel, PCDT, incorporação, CONITEC).
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import math
import logging
from utils import (
    carregar_base_enatjus,
    criar_pasta_outputs,
    salvar_excel,
    intervalo_confianca_proporcao,
    processar_subconjunto,
    grafico_barras_sucesso,
    logger
)

# Configurar pandas
pd.set_option('display.max_columns', None)


def preparar_dados_divergencia(df):
    """
    Prepara dados para análise de divergências regionais.

    Args:
        df (pd.DataFrame): DataFrame completo

    Returns:
        pd.DataFrame: DataFrame preparado
    """
    logger.info("Preparando dados para análise de divergências...")

    # Selecionar colunas relevantes
    colunas = [
        'idNotaTecnica', 'arquivo', 'origem_tratada',
        'selIndicacaoConformidade', 'selPrevistoProtocolo',
        'selDisponivelSus', 'selRecomendacaoConitec', 'selConclusao'
    ]

    df_prep = df[colunas].copy()

    # Filtrar apenas Favorável e Não favorável
    df_prep = df_prep[df_prep['selConclusao'].isin(['F', 'N'])]

    logger.info(f"Dados preparados: {len(df_prep)} registros")
    return df_prep


def calcular_taxas_concessao(df, lista_inst, pasta_output='outputs'):
    """
    Calcula taxas de concessão geral por instituição.

    Args:
        df (pd.DataFrame): DataFrame preparado
        lista_inst (list): Lista de instituições a analisar
        pasta_output (str): Pasta para salvar resultados

    Returns:
        pd.DataFrame: DataFrame com taxas de concessão
    """
    logger.info("Calculando taxas de concessão...")

    resultados = []

    for inst in lista_inst:
        inst_data = df[df['origem_tratada'] == inst]
        qtd_total = len(inst_data)

        if qtd_total > 0:
            # selConclusao: 'F' = Favorável
            favoravel_count = inst_data[inst_data['selConclusao'] == 'F'].shape[0]
            proporcao_favoravel = favoravel_count / qtd_total

            limite_inferior, limite_superior = intervalo_confianca_proporcao(proporcao_favoravel, qtd_total)

            resultados.append({
                'Órgão de ATS': inst,
                'Nº de pareceres': qtd_total,
                'Proporção Favorável': proporcao_favoravel,
                'IC Inferior': limite_inferior,
                'IC Superior': limite_superior
            })

    df_resultados = pd.DataFrame(resultados)
    df_resultados = df_resultados.sort_values(by='Proporção Favorável', ascending=True)
    df_resultados['margem_de_erro'] = ((df_resultados['IC Superior'] - df_resultados['IC Inferior'])/2).round(3)*100

    salvar_excel(df_resultados, 'taxas_concessao.xlsx', pasta_output)
    logger.info(f"Taxas de concessão salvas: {len(df_resultados)} instituições")

    return df_resultados


def calcular_taxas_subconjuntos(df, pasta_output='outputs'):
    """
    Calcula taxas de concessão por subconjuntos específicos.

    Args:
        df (pd.DataFrame): DataFrame preparado
        pasta_output (str): Pasta para salvar resultados

    Returns:
        pd.DataFrame: DataFrame com taxas por subconjunto
    """
    logger.info("Calculando taxas por subconjuntos...")

    resultados_finais = []

    # Definir filtros para subconjuntos
    # selIndicacaoConformidade: 'N' = Não (offlabel)
    # selPrevistoProtocolo: 'N' = Não (não previsto em PCDT)
    # selDisponivelSus: 'N' = Não (não disponível no SUS/não incorporado)
    # selRecomendacaoConitec: 'D' = Não Recomendada (Desfavorável)
    colunas_filtro = ['selIndicacaoConformidade', 'selPrevistoProtocolo', 'selDisponivelSus', 'selRecomendacaoConitec']
    valores_filtro = ['N', 'N', 'N', 'D']

    # Não aplicar filtro de min_observacoes aqui pois as instituições já foram pré-selecionadas
    # com base em terem pelo menos pareceres suficientes no geral
    for coluna, valor in zip(colunas_filtro, valores_filtro):
        resultados_finais.extend(processar_subconjunto(df, coluna, valor, 100))

    # Adicionar o conjunto geral
    resultados_finais.extend(processar_subconjunto(df, 'origem_tratada', '', 100, geral=True))

    df_resultados = pd.DataFrame(resultados_finais)
    df_resultados = df_resultados.sort_values(by='Proporção Favorável', ascending=False)
    df_resultados['margem_de_erro'] = ((df_resultados['IC Superior'] - df_resultados['IC Inferior']) / 2).round(3) * 100

    salvar_excel(df_resultados, 'taxas_concessao_subconjuntos.xlsx', pasta_output)
    logger.info(f"Taxas por subconjuntos salvas: {len(df_resultados)} registros")

    return df_resultados


def gerar_graficos_taxas(df_taxas, df_subconjuntos, pasta_output='outputs'):
    """
    Gera gráficos de barras para taxas de concessão.

    Args:
        df_taxas (pd.DataFrame): DataFrame com taxas gerais
        df_subconjuntos (pd.DataFrame): DataFrame com taxas por subconjunto
        pasta_output (str): Pasta para salvar gráficos
    """
    logger.info("Gerando gráficos de taxas de concessão...")

    # Gráfico geral (aumentar largura para 24 instituições)
    grafico_barras_sucesso(df_taxas, x=24, y=9, output_path=os.path.join(pasta_output, 'grafico_taxas_gerais.png'))

    # Gráficos por subconjunto
    for coluna in df_subconjuntos['Coluna'].unique():
        if coluna != 'Geral':
            df_filtrado = df_subconjuntos[df_subconjuntos['Coluna'] == coluna]
            nome_arquivo = f"grafico_{coluna}.png"
            grafico_barras_sucesso(df_filtrado, x=15, output_path=os.path.join(pasta_output, nome_arquivo))

    logger.info("Gráficos salvos com sucesso")


def main():
    """
    Função principal que executa todas as análises.
    """
    logger.info("=" * 60)
    logger.info("INICIANDO ANÁLISE DE DIVERGÊNCIAS REGIONAIS")
    logger.info("=" * 60)

    # Criar pasta de outputs
    pasta_output = 'outputs'
    criar_pasta_outputs(pasta_output)

    # Carregar base de dados
    caminho_base = os.path.join('..', 'base_enatjus_2025-1.parquet')
    df = carregar_base_enatjus(caminho_base)

    # Preparar dados
    df_prep = preparar_dados_divergencia(df)

    # Selecionar instituições relevantes (top 24 com pareceres válidos)
    lista_inst = df_prep.loc[df_prep['origem_tratada'] != 'NÃO_PREENCHIDO']['origem_tratada'].value_counts().head(24).index.tolist()
    logger.info(f"Analisando {len(lista_inst)} instituições")

    # Filtrar dados para instituições relevantes
    df_filtrado = df_prep.loc[df_prep['origem_tratada'].isin(lista_inst)].copy()

    # Calcular taxas
    df_taxas = calcular_taxas_concessao(df_filtrado, lista_inst, pasta_output)
    df_subconjuntos = calcular_taxas_subconjuntos(df_filtrado, pasta_output)

    # Gerar gráficos
    gerar_graficos_taxas(df_taxas, df_subconjuntos, pasta_output)

    logger.info("=" * 60)
    logger.info("ANÁLISE DE DIVERGÊNCIAS REGIONAIS CONCLUÍDA COM SUCESSO")
    logger.info(f"Resultados salvos em: {pasta_output}/")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
