"""
Análise descritiva geral por instituição responsável.

Este script gera estatísticas descritivas agregadas para instituições
com pelo menos 100 pareceres, incluindo informações sobre demandantes,
características dos processos e resultados.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import logging
from utils import (
    carregar_base_enatjus,
    criar_pasta_outputs,
    salvar_excel,
    MAPA_VALORES,
    logger
)

# Configurar pandas para exibir todas as colunas
pd.set_option('display.max_columns', None)


def preparar_dados(df):
    """
    Prepara dados selecionando colunas relevantes e filtrando.

    Args:
        df (pd.DataFrame): DataFrame completo

    Returns:
        pd.DataFrame: DataFrame preparado
    """
    logger.info("Preparando dados...")

    # Selecionar colunas relevantes
    colunas = [
        'idNotaTecnica', 'arquivo', 'origem_tratada',
        'selStaGenero', 'selDefensoriaPublica', 'selEsfera',
        'selRegistroAnvisa', 'selUsoContinuo', 'selIndicacaoConformidade',
        'selPrevistoProtocolo', 'selDisponivelSus', 'selOncologico',
        'selExisteGenerico', 'selExisteBiossimilar', 'selRecomendacaoConitec',
        'selConclusao', 'selEvidenciaCientifica', 'selAlegacaoUrgencia',
        'selAlegacaoUrgenciaJustificativaNotaTecnica', 'selApoioTutoria'
    ]

    df_prep = df[colunas].copy()

    # Filtrar apenas pareceres com conclusão Favorável ou Não favorável
    df_prep = df_prep[df_prep['selConclusao'].isin(['F', 'N'])]

    logger.info(f"Dados preparados: {len(df_prep)} registros")
    return df_prep


def gerar_descritivos_gerais(df, pasta_output='outputs'):
    """
    Gera tabela descritiva geral por instituição (mínimo 100 observações).

    Args:
        df (pd.DataFrame): DataFrame preparado
        pasta_output (str): Pasta para salvar os resultados
    """
    logger.info("Gerando descritivos gerais...")

    # Filtrar instituições com pelo menos 100 pareceres
    inst_counts = df['origem_tratada'].value_counts()
    inst_validos = inst_counts[inst_counts >= 100].index
    df_filtrado = df[df['origem_tratada'].isin(inst_validos)]

    logger.info(f"Instituições com >= 100 pareceres: {len(inst_validos)}")

    # Colunas a analisar (exceto identificadores)
    cols_analisar = [col for col in df.columns if col not in ['idNotaTecnica', 'arquivo', 'origem_tratada']]

    # Lista para armazenar os DataFrames parciais
    dfs = []

    for col in cols_analisar:
        # Calcular proporções por instituição
        vc = df_filtrado.groupby('origem_tratada')[col].value_counts(normalize=True, dropna=False).round(3) * 100
        df_vc = vc.unstack(fill_value=0)
        df_vc.columns = [f"{col}_{str(val)}" for val in df_vc.columns]
        dfs.append(df_vc)

    # Concatenar todos os DataFrames
    df_resultado = pd.concat(dfs, axis=1)

    # Adicionar contagem de observações
    df_resultado.insert(0, 'origem_tratada', df_resultado.index)
    df_resultado.insert(1, 'n_observacoes',
                       df_filtrado['origem_tratada'].value_counts().reindex(df_resultado.index, fill_value=0).values)

    df_resultado = df_resultado.reset_index(drop=True)

    # Remover colunas redundantes (valores que são complemento de outros)
    colunas_remover = [
        'selStaGenero_M', 'selStaGenero_NÃO_PREENCHIDO',
        'selRegistroAnvisa_NÃO_PREENCHIDO', 'selApoioTutoria_NÃO_PREENCHIDO',
        'selConclusao_NÃO_PREENCHIDO'
    ]

    # Remover apenas as colunas que existem no DataFrame
    colunas_remover_existentes = [col for col in colunas_remover if col in df_resultado.columns]
    if colunas_remover_existentes:
        df_resultado = df_resultado.drop(columns=colunas_remover_existentes)

    # Remover linha de "NÃO_PREENCHIDO" se existir
    if 'NÃO_PREENCHIDO' in df_resultado['origem_tratada'].values:
        df_resultado = df_resultado[df_resultado['origem_tratada'] != 'NÃO_PREENCHIDO']

    salvar_excel(df_resultado, 'df_descGeral.xlsx', pasta_output)
    logger.info(f"Descritivos gerais salvos: {len(df_resultado)} instituições")

    return df_resultado


def gerar_analise_demandantes(df_resultado, pasta_output='outputs'):
    """
    Gera análise focada em características dos demandantes.

    Args:
        df_resultado (pd.DataFrame): DataFrame com descritivos gerais
        pasta_output (str): Pasta para salvar os resultados
    """
    logger.info("Gerando análise de demandantes...")

    # Selecionar colunas relevantes para demandantes
    colunas_demandantes = ['origem_tratada', 'n_observacoes']

    # Adicionar colunas que existem no DataFrame
    colunas_possiveis = [
        'selStaGenero_F',
        'selDefensoriaPublica_D',
        'selDefensoriaPublica_M',
        'selDefensoriaPublica_NÃO_PREENCHIDO',
        'selEsfera_E',
        'selEsfera_F',
        'selEsfera_NÃO_PREENCHIDO',
        'selConclusao_F',
        'selAlegacaoUrgencia_N',
        'selApoioTutoria_S'
    ]

    colunas_demandantes.extend([col for col in colunas_possiveis if col in df_resultado.columns])

    df_demandantes = df_resultado[colunas_demandantes].copy()

    salvar_excel(df_demandantes, 'demandantes.xlsx', pasta_output)
    logger.info(f"Análise de demandantes salva: {len(df_demandantes)} instituições")


def main():
    """
    Função principal que executa todas as análises.
    """
    logger.info("=" * 60)
    logger.info("INICIANDO ANÁLISE GERAL")
    logger.info("=" * 60)

    # Criar pasta de outputs
    pasta_output = 'outputs'
    criar_pasta_outputs(pasta_output)

    # Carregar base de dados
    caminho_base = os.path.join('..', 'base_enatjus_2025-1.parquet')
    df = carregar_base_enatjus(caminho_base)

    # Preparar dados
    df_prep = preparar_dados(df)

    # Gerar análises
    df_resultado = gerar_descritivos_gerais(df_prep, pasta_output)
    gerar_analise_demandantes(df_resultado, pasta_output)

    logger.info("=" * 60)
    logger.info("ANÁLISE GERAL CONCLUÍDA COM SUCESSO")
    logger.info(f"Resultados salvos em: {pasta_output}/")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
