"""
Análise descritiva de pedidos por CID, grupos de doenças e princípios ativos.

Este script analisa a distribuição de pedidos de pareceres técnicos por:
- Grupos de doenças (CID)
- CIDs específicos mais comuns
- Princípios ativos mais solicitados
Separando análises entre Hospital Israelita Albert Einstein e demais instituições.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import logging
from utils import (
    carregar_base_enatjus,
    processar_cid,
    criar_pasta_outputs,
    salvar_excel,
    logger
)

# Configurar pandas para exibir todas as colunas
pd.set_option('display.max_columns', None)


def filtrar_dados_relevantes(df):
    """
    Filtra e seleciona colunas relevantes para análise de pedidos.

    Args:
        df (pd.DataFrame): DataFrame completo

    Returns:
        pd.DataFrame: DataFrame filtrado
    """
    colunas = ['idNotaTecnica', 'arquivo', 'origem_tratada', 'txtCid', 'txtDcb']
    df_filtrado = df[colunas].copy()

    logger.info(f"Dados filtrados: {len(df_filtrado)} registros")
    return df_filtrado


def analisar_grupos_doencas(df_quali, pasta_output='outputs'):
    """
    Analisa a distribuição de grupos de doenças (CID) por instituição.

    Args:
        df_quali (pd.DataFrame): DataFrame com dados processados
        pasta_output (str): Pasta para salvar os resultados
    """
    logger.info("Analisando grupos de doenças...")

    # Análise para outras instituições (exceto Nacional)
    outros = df_quali.loc[df_quali['origem_tratada'] != 'Nacional']
    grupoD_outros = outros['CID4-Tipo'].value_counts()
    salvar_excel(grupoD_outros.to_frame('Contagem').reset_index(), 'grupoD_outros.xlsx', pasta_output)

    # Análise para Nacional (Hospital Israelita Albert Einstein)
    nacional = df_quali.loc[df_quali['origem_tratada'] == 'Nacional']
    grupoD_nacional = nacional['CID4-Tipo'].value_counts()
    salvar_excel(grupoD_nacional.to_frame('Contagem').reset_index(), 'grupoD_nacional.xlsx', pasta_output)

    logger.info(f"Grupos de doenças - Outros: {len(grupoD_outros)} categorias")
    logger.info(f"Grupos de doenças - Nacional: {len(grupoD_nacional)} categorias")


def analisar_cids_especificos(df_quali, pasta_output='outputs'):
    """
    Analisa os CIDs específicos mais comuns por instituição.

    Args:
        df_quali (pd.DataFrame): DataFrame com dados processados
        pasta_output (str): Pasta para salvar os resultados
    """
    logger.info("Analisando CIDs específicos...")

    # Top 10 CIDs - Outras instituições
    outros = df_quali.loc[df_quali['origem_tratada'] != 'Nacional']
    cids_outros = outros['CID3'].value_counts().head(10)
    salvar_excel(cids_outros.to_frame('Contagem').reset_index(), 'doencas_outros.xlsx', pasta_output)

    # Top 10 CIDs - Nacional
    nacional = df_quali.loc[df_quali['origem_tratada'] == 'Nacional']
    cids_nacional = nacional['CID3'].value_counts().head(10)
    salvar_excel(cids_nacional.to_frame('Contagem').reset_index(), 'doencas_nacional.xlsx', pasta_output)

    logger.info(f"Top 10 CIDs - Outros: {cids_outros.iloc[0] if len(cids_outros) > 0 else 'N/A'}")
    logger.info(f"Top 10 CIDs - Nacional: {cids_nacional.iloc[0] if len(cids_nacional) > 0 else 'N/A'}")


def analisar_principios_ativos(df_quali, pasta_output='outputs'):
    """
    Analisa princípios ativos mais solicitados e seus CIDs principais.

    Args:
        df_quali (pd.DataFrame): DataFrame com dados processados
        pasta_output (str): Pasta para salvar os resultados
    """
    logger.info("Analisando princípios ativos...")

    # Padronizar nomes dos princípios ativos
    df_quali['principio'] = df_quali['txtDcb'].str.lower()

    # Análise para outras instituições
    outros = df_quali.loc[df_quali['origem_tratada'] != 'Nacional']
    top_principios_outros = outros['principio'].value_counts().head(10)

    resultado_outros = pd.DataFrame({
        'Princípio': top_principios_outros.index,
        'Contagem': top_principios_outros.values,
        'CID3 Principal': None
    })

    for i, principio in enumerate(resultado_outros['Princípio']):
        df_principio = outros[outros['principio'] == principio]
        if not df_principio.empty and not df_principio['CID3'].value_counts().empty:
            cid_mais_comum = df_principio['CID3'].value_counts().index[0]
            resultado_outros.at[i, 'CID3 Principal'] = cid_mais_comum

    salvar_excel(resultado_outros, 'principio_outros.xlsx', pasta_output)

    # Análise para Nacional
    nacional = df_quali.loc[df_quali['origem_tratada'] == 'Nacional']
    top_principios_nacional = nacional['principio'].value_counts().head(10)

    resultado_nacional = pd.DataFrame({
        'Princípio': top_principios_nacional.index,
        'Contagem': top_principios_nacional.values,
        'CID3 Principal': None
    })

    for i, principio in enumerate(resultado_nacional['Princípio']):
        df_principio = nacional[nacional['principio'] == principio]
        if not df_principio.empty and not df_principio['CID3'].value_counts().empty:
            cid_mais_comum = df_principio['CID3'].value_counts().index[0]
            resultado_nacional.at[i, 'CID3 Principal'] = cid_mais_comum

    salvar_excel(resultado_nacional, 'principio_nacional.xlsx', pasta_output)

    logger.info("Análise de princípios ativos concluída")


def main():
    """
    Função principal que executa todas as análises.
    """
    logger.info("=" * 60)
    logger.info("INICIANDO ANÁLISE DE PEDIDOS")
    logger.info("=" * 60)

    # Criar pasta de outputs
    pasta_output = 'outputs'
    criar_pasta_outputs(pasta_output)

    # Carregar base de dados
    caminho_base = os.path.join('..', 'base_enatjus_2025-1.parquet')
    df = carregar_base_enatjus(caminho_base)

    # Filtrar dados relevantes
    df_quali = filtrar_dados_relevantes(df)

    # Processar CIDs
    df_quali = processar_cid(df_quali)

    # Executar análises
    analisar_grupos_doencas(df_quali, pasta_output)
    analisar_cids_especificos(df_quali, pasta_output)
    analisar_principios_ativos(df_quali, pasta_output)

    logger.info("=" * 60)
    logger.info("ANÁLISE DE PEDIDOS CONCLUÍDA COM SUCESSO")
    logger.info(f"Resultados salvos em: {pasta_output}/")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
