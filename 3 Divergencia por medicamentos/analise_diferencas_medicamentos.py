"""
Análise de diferenças entre instituições para medicamentos específicos.

Este script analisa a base de controle gerada pelo script anterior,
identificando divergências significativas entre instituições nas taxas
de concessão para combinações específicas de medicamento + CID.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import logging
from utils import (
    criar_pasta_outputs,
    salvar_excel,
    logger
)

# Configurar pandas
pd.set_option('display.max_columns', None)


def carregar_base_controle(pasta_input='outputs'):
    """
    Carrega a base de controle gerada anteriormente.

    Args:
        pasta_input (str): Pasta onde está a base de controle

    Returns:
        pd.DataFrame: Base de controle carregada
    """
    logger.info("Carregando base de controle...")

    caminho = os.path.join(pasta_input, 'controle_por_tratamento_e_por_CID.xlsx')
    df = pd.read_excel(caminho)

    logger.info(f"Base de controle carregada: {len(df)} registros")
    return df


def analisar_diferencas_entre_instituicoes(df_base, pasta_output='outputs'):
    """
    Analisa diferenças entre instituições para mesmas combinações tecnologia+CID.

    Args:
        df_base (pd.DataFrame): Base de controle
        pasta_output (str): Pasta para salvar resultados

    Returns:
        pd.DataFrame: DataFrame com análise de diferenças
    """
    logger.info("Analisando diferenças entre instituições...")

    # Filtrar instituições (excluir Nacional)
    df_filtrado = df_base[df_base['Órgão de ATS'] != 'Nacional']

    # Agrupar por Tecnologia e CID, contar instituições únicas
    tecnologias_validas = df_filtrado.groupby(['Tecnologia', 'CID'])['Órgão de ATS'].nunique()
    # Manter apenas combinações avaliadas por >= 2 instituições
    tecnologias_validas = tecnologias_validas[tecnologias_validas >= 2].index

    # Filtrar DataFrame
    df_filtrado = df_filtrado.set_index(['Tecnologia', 'CID'])
    df_filtrado = df_filtrado.loc[df_filtrado.index.isin(tecnologias_validas)].reset_index()

    logger.info(f"Combinações avaliadas por >= 2 instituições: {len(df_filtrado)}")

    # Identificar órgãos mais e menos favoráveis para cada combinação
    resultados = []

    for (tecnologia, cid), grupo in df_filtrado.groupby(['Tecnologia', 'CID']):
        # Encontrar máximos e mínimos
        max_fav = grupo[grupo['Favorável'] == grupo['Favorável'].max()]
        min_fav = grupo[grupo['Favorável'] == grupo['Favorável'].min()]

        # Tratar empates para o máximo
        if len(max_fav) > 1:
            orgao_max = "/".join(max_fav['Órgão de ATS'])
            num_max = "/".join(map(str, max_fav['Nº de pareceres']))
            valor_max = max_fav['Favorável'].iloc[0]
        else:
            orgao_max = max_fav['Órgão de ATS'].iloc[0]
            num_max = max_fav['Nº de pareceres'].iloc[0]
            valor_max = max_fav['Favorável'].iloc[0]

        # Tratar empates para o mínimo
        if len(min_fav) > 1:
            orgao_min = "/".join(min_fav['Órgão de ATS'])
            num_min = "/".join(map(str, min_fav['Nº de pareceres']))
            valor_min = min_fav['Favorável'].iloc[0]
        else:
            orgao_min = min_fav['Órgão de ATS'].iloc[0]
            num_min = min_fav['Nº de pareceres'].iloc[0]
            valor_min = min_fav['Favorável'].iloc[0]

        # Calcular total de pareceres
        total_pareceres = grupo['Nº de pareceres'].sum()

        resultados.append({
            'Tecnologia': tecnologia,
            'CID': cid,
            'Total de pareceres': total_pareceres,
            'Órgão de ATS + Favorável': orgao_max,
            'Nº de pareceres do Órgão de ATS + favorável': num_max,
            'Valor em favorável do Órgão de ATS + favorável': valor_max,
            'Órgão de ATS - Favorável': orgao_min,
            'Nº de pareceres do Órgão de ATS - favorável': num_min,
            'Valor em favorável do Órgão de ATS - favorável': valor_min,
            'Diferença entre o órgão + favorável e o - favorável': valor_max - valor_min
        })

    df_difs = pd.DataFrame(resultados)
    salvar_excel(df_difs, 'diferencas_medicamentos.xlsx', pasta_output)

    logger.info(f"Análise de diferenças salva: {len(df_difs)} combinações")

    # Estatísticas de diferenças
    dif_100 = df_difs[df_difs['Diferença entre o órgão + favorável e o - favorável'] == 100].shape[0]
    dif_80 = df_difs[df_difs['Diferença entre o órgão + favorável e o - favorável'] >= 80].shape[0]
    dif_50 = df_difs[df_difs['Diferença entre o órgão + favorável e o - favorável'] >= 50].shape[0]
    dif_20 = df_difs[df_difs['Diferença entre o órgão + favorável e o - favorável'] >= 20].shape[0]

    logger.info(f"Diferença de 100%: {dif_100} combinações")
    logger.info(f"Diferença >= 80%: {dif_80} combinações")
    logger.info(f"Diferença >= 50%: {dif_50} combinações")
    logger.info(f"Diferença >= 20%: {dif_20} combinações")

    return df_difs


def comparar_com_nacional(df_base, pasta_output='outputs'):
    """
    Compara cada instituição com a Nacional para mesmas tecnologias+CID.

    Args:
        df_base (pd.DataFrame): Base de controle
        pasta_output (str): Pasta para salvar resultados

    Returns:
        pd.DataFrame: DataFrame com comparações
    """
    logger.info("Comparando instituições com Nacional...")

    # Filtrar dados da Nacional
    df_nacional = df_base[df_base['Órgão de ATS'] == 'Nacional']

    comparacao_resultados = []

    # Iterar sobre cada medicamento e CID avaliados pela Nacional
    for index, row in df_nacional.iterrows():
        med = row['Tecnologia']
        cid = row['CID']
        nacional_num = row['Nº de pareceres']
        nacional_taxa = row.get('Favorável', 0)

        # Filtrar outras instituições que avaliaram o mesmo medicamento e CID
        outras_inst_data = df_base[
            (df_base['Tecnologia'] == med) &
            (df_base['CID'] == cid) &
            (df_base['Órgão de ATS'] != 'Nacional')
        ]

        # Iterar sobre as outras instituições
        for _, outra_inst_row in outras_inst_data.iterrows():
            inst = outra_inst_row['Órgão de ATS']
            inst_num = outra_inst_row['Nº de pareceres']
            inst_taxa = outra_inst_row.get('Favorável', 0)

            # Determinar quem teve a maior taxa
            melhor = 'Nacional' if nacional_taxa > inst_taxa else inst

            comparacao_resultados.append({
                'Medicamento': med,
                'CID': cid,
                'Instituição': inst,
                'Instituição_num_pareceres': inst_num,
                'Instituição_taxa': inst_taxa,
                'Nacional_num_pareceres': nacional_num,
                'Nacional_taxa': nacional_taxa,
                'Melhor': melhor,
                'Ganho': abs(nacional_taxa - inst_taxa)
            })

    df_comparacao = pd.DataFrame(comparacao_resultados)
    salvar_excel(df_comparacao, 'comparacao_instituicoes_nacional.xlsx', pasta_output)

    logger.info(f"Comparação com Nacional salva: {len(df_comparacao)} registros")

    # Estatísticas
    if not df_comparacao.empty:
        contagem_melhor = df_comparacao['Melhor'].value_counts()
        logger.info(f"Instituições com melhor taxa: \n{contagem_melhor}")

    return df_comparacao


def analisar_maiores_ganhos(df_comparacao, pasta_output='outputs'):
    """
    Analisa os maiores ganhos por instituição (escolhendo Nacional vs própria instituição).

    Args:
        df_comparacao (pd.DataFrame): DataFrame com comparações
        pasta_output (str): Pasta para salvar resultados
    """
    logger.info("Analisando maiores ganhos por instituição...")

    maiores_ganhos = []

    for inst in df_comparacao['Instituição'].unique():
        inst_data = df_comparacao[df_comparacao['Instituição'] == inst]

        # Ganho máximo optando por Nacional
        nacional_data = inst_data[inst_data['Melhor'] == 'Nacional']
        if not nacional_data.empty:
            max_ganho_nacional = nacional_data['Ganho'].max()
            max_ganho_nacional_data = nacional_data[nacional_data['Ganho'] == max_ganho_nacional]

            for idx, row in max_ganho_nacional_data.iterrows():
                maiores_ganhos.append({
                    'Instituição': inst,
                    'Ganho escolhendo': 'Nacional',
                    'Medicamento': row['Medicamento'],
                    'CID': row['CID'],
                    'Nacional_taxa': f"{row['Nacional_taxa']:.1f}% (n={row['Nacional_num_pareceres']})",
                    'Instituição_taxa': f"{row['Instituição_taxa']:.1f}% (n={row['Instituição_num_pareceres']})",
                    'Ganho': max_ganho_nacional
                })

        # Ganho máximo optando pela própria instituição
        inst_melhor_data = inst_data[inst_data['Melhor'] == inst]
        if not inst_melhor_data.empty:
            max_ganho_inst = inst_melhor_data['Ganho'].max()
            max_ganho_inst_data = inst_melhor_data[inst_melhor_data['Ganho'] == max_ganho_inst]

            for idx, row in max_ganho_inst_data.iterrows():
                maiores_ganhos.append({
                    'Instituição': inst,
                    'Ganho escolhendo': inst,
                    'Medicamento': row['Medicamento'],
                    'CID': row['CID'],
                    'Nacional_taxa': f"{row['Nacional_taxa']:.1f}% (n={row['Nacional_num_pareceres']})",
                    'Instituição_taxa': f"{row['Instituição_taxa']:.1f}% (n={row['Instituição_num_pareceres']})",
                    'Ganho': max_ganho_inst
                })

    df_maiores_ganhos = pd.DataFrame(maiores_ganhos)

    # Reordenar colunas
    cols = ['Instituição', 'Ganho escolhendo', 'Medicamento', 'CID', 'Nacional_taxa', 'Instituição_taxa', 'Ganho']
    df_maiores_ganhos = df_maiores_ganhos[cols]

    salvar_excel(df_maiores_ganhos, 'maiores_ganhos_instituicoes_e_nacional.xlsx', pasta_output)
    logger.info(f"Maiores ganhos salvos: {len(df_maiores_ganhos)} registros")


def main():
    """
    Função principal que executa todas as análises.
    """
    logger.info("=" * 60)
    logger.info("INICIANDO ANÁLISE DE DIFERENÇAS POR MEDICAMENTOS")
    logger.info("=" * 60)

    # Criar pasta de outputs
    pasta_output = 'outputs'
    criar_pasta_outputs(pasta_output)

    # Carregar base de controle
    df_base = carregar_base_controle(pasta_input='outputs')

    # Análise de diferenças entre instituições
    df_difs = analisar_diferencas_entre_instituicoes(df_base, pasta_output)

    # Comparação com Nacional
    df_comparacao = comparar_com_nacional(df_base, pasta_output)

    # Analisar maiores ganhos
    if not df_comparacao.empty:
        analisar_maiores_ganhos(df_comparacao, pasta_output)

    logger.info("=" * 60)
    logger.info("ANÁLISE DE DIFERENÇAS POR MEDICAMENTOS CONCLUÍDA")
    logger.info(f"Resultados salvos em: {pasta_output}/")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
