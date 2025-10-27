"""
Geração de base de dados para análise de diferenças por medicamentos.

Este script cria uma base de controle agregando pareceres por combinação
de medicamento (princípio ativo) e CID, filtrando apenas combinações
com número mínimo de observações.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import unidecode
import logging
from utils import (
    carregar_base_enatjus,
    criar_pasta_outputs,
    salvar_excel,
    logger
)

# Configurar pandas
pd.set_option('display.max_columns', None)


def preparar_dados_medicamentos(df):
    """
    Prepara dados para análise por medicamentos.

    Args:
        df (pd.DataFrame): DataFrame completo

    Returns:
        pd.DataFrame: DataFrame preparado
    """
    logger.info("Preparando dados para análise por medicamentos...")

    # Selecionar colunas relevantes
    colunas = [
        'idNotaTecnica', 'arquivo', 'origem_tratada', 'txtCid', 'txtDcb', 'selConclusao'
    ]

    df_prep = df[colunas].copy()

    # Extrair CID simplificado (formato: A00, B12, etc.)
    df_prep['cid_simplificado'] = df_prep['txtCid'].str.extract(r'([A-Z]\d{2})')

    # Padronizar nome do princípio ativo (tecnologia)
    # Remove espaços, acentos e converte para minúsculas
    df_prep['tecnologia_principio'] = (df_prep['txtDcb']
                                        .astype(str)
                                        .str.lower()
                                        .str.replace(' ', '', regex=False)
                                        .apply(unidecode.unidecode))

    # Filtrar apenas Favorável e Não favorável
    df_prep = df_prep[df_prep['selConclusao'].isin(['F', 'N'])]

    logger.info(f"Dados preparados: {len(df_prep)} registros")
    return df_prep


def filtrar_combinacoes_relevantes(df, min_observacoes=10):
    """
    Filtra apenas combinações de CID + medicamento com número mínimo de observações.

    Args:
        df (pd.DataFrame): DataFrame preparado
        min_observacoes (int): Número mínimo de observações por combinação

    Returns:
        pd.DataFrame: DataFrame filtrado
    """
    logger.info(f"Filtrando combinações com >= {min_observacoes} observações...")

    # Selecionar instituições relevantes (top 24)
    lista_inst = df.loc[df['origem_tratada'] != 'NÃO_PREENCHIDO']['origem_tratada'].value_counts().head(24).index.tolist()
    df_filtrado = df.loc[df['origem_tratada'].isin(lista_inst)].copy()

    # Contar combinações de cid_simplificado + tecnologia_principio
    contagem_combinacoes = df_filtrado.groupby(['cid_simplificado', 'tecnologia_principio']).size().reset_index(name='contagens')

    # Filtrar combinações que aparecem >= min_observacoes vezes
    combinacoes_filtradas = contagem_combinacoes[contagem_combinacoes['contagens'] >= min_observacoes]

    # Mesclar com DataFrame original para obter linhas completas
    df_controle = df_filtrado.merge(
        combinacoes_filtradas[['cid_simplificado', 'tecnologia_principio']],
        on=['cid_simplificado', 'tecnologia_principio']
    )

    logger.info(f"Combinações relevantes: {len(combinacoes_filtradas)}")
    logger.info(f"Registros após filtro: {len(df_controle)}")

    return df_controle


def gerar_base_controle(df_controle, pasta_output='outputs'):
    """
    Gera base de controle agregada por instituição, tecnologia e CID.

    Args:
        df_controle (pd.DataFrame): DataFrame com combinações filtradas
        pasta_output (str): Pasta para salvar resultados

    Returns:
        pd.DataFrame: Base de controle gerada
    """
    logger.info("Gerando base de controle por tratamento e CID...")

    resultados = []
    lista_instituicoes = df_controle['origem_tratada'].unique()

    for inst in lista_instituicoes:
        logger.info(f"Processando instituição: {inst}")

        lista_meds = df_controle.loc[df_controle['origem_tratada'] == inst]['tecnologia_principio'].unique()

        for med in lista_meds:
            lista_cids = df_controle.loc[
                (df_controle['origem_tratada'] == inst) &
                (df_controle['tecnologia_principio'] == med)
            ]['cid_simplificado'].unique()

            for cid in lista_cids:
                # Filtrar dados
                filtro = df_controle.loc[
                    (df_controle['origem_tratada'] == inst) &
                    (df_controle['tecnologia_principio'] == med) &
                    (df_controle['cid_simplificado'] == cid)
                ]
                qtd_total = len(filtro)

                # Verificar se o número de registros é maior que 10
                if qtd_total > 10:
                    # Calcular estatísticas de conclusão
                    conclusao_stats = filtro['selConclusao'].value_counts(normalize=True).round(3) * 100

                    resultado = {
                        'Órgão de ATS': inst,
                        'Tecnologia': med,
                        'CID': cid,
                        'Nº de pareceres': qtd_total
                    }

                    # Adicionar conclusões como colunas
                    # F = Favorável, N = Não favorável
                    resultado['Favorável'] = conclusao_stats.get('F', 0)
                    resultado['Não favorável'] = conclusao_stats.get('N', 0)

                    resultados.append(resultado)

    df_resultados = pd.DataFrame(resultados)

    # Salvar base de controle
    salvar_excel(df_resultados, 'controle_por_tratamento_e_por_CID.xlsx', pasta_output)
    logger.info(f"Base de controle gerada: {len(df_resultados)} registros")

    return df_resultados


def gerar_exemplo_base(df, pasta_output='outputs'):
    """
    Gera arquivo Excel com exemplo das primeiras linhas da base.

    Args:
        df (pd.DataFrame): DataFrame original
        pasta_output (str): Pasta para salvar resultado
    """
    logger.info("Gerando arquivo exemplo da base...")

    df_exemplo = df.head(30)
    salvar_excel(df_exemplo, 'exemplo_base.xlsx', pasta_output)

    logger.info("Arquivo exemplo gerado")


def main():
    """
    Função principal que executa todas as operações.
    """
    logger.info("=" * 60)
    logger.info("INICIANDO GERAÇÃO DE BASE DE DIFERENÇAS POR MEDICAMENTOS")
    logger.info("=" * 60)

    # Criar pasta de outputs
    pasta_output = 'outputs'
    criar_pasta_outputs(pasta_output)

    # Carregar base de dados
    caminho_base = os.path.join('..', 'base_enatjus_2025-1.parquet')
    df = carregar_base_enatjus(caminho_base)

    # Gerar exemplo da base
    gerar_exemplo_base(df, pasta_output)

    # Preparar dados
    df_prep = preparar_dados_medicamentos(df)

    # Filtrar combinações relevantes
    df_controle = filtrar_combinacoes_relevantes(df_prep, min_observacoes=10)

    # Gerar base de controle
    df_resultados = gerar_base_controle(df_controle, pasta_output)

    logger.info("=" * 60)
    logger.info("GERAÇÃO DE BASE CONCLUÍDA COM SUCESSO")
    logger.info(f"Base de controle: {len(df_resultados)} registros")
    logger.info(f"Resultados salvos em: {pasta_output}/")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
