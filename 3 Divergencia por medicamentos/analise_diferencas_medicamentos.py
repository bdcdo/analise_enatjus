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


def analisar_diferencas_entre_instituicoes(df_base, pasta_output='outputs', min_pareceres=10):
    """
    Analisa diferenças entre instituições para mesmas combinações tecnologia+CID.

    Args:
        df_base (pd.DataFrame): Base de controle
        pasta_output (str): Pasta para salvar resultados
        min_pareceres (int): Número mínimo de pareceres por instituição para incluir no conjunto

    Returns:
        pd.DataFrame: DataFrame com análise de diferenças
    """
    logger.info("Analisando diferenças entre instituições...")

    # Total de combinações inicial
    total_inicial = df_base[df_base['Órgão de ATS'] != 'Nacional'].groupby(['Tecnologia', 'CID']).ngroups
    logger.info(f"Total de combinações Tecnologia+CID (excluindo Nacional): {total_inicial}")

    # Filtrar instituições (excluir Nacional)
    df_filtrado = df_base[df_base['Órgão de ATS'] != 'Nacional'].copy()

    # Filtrar apenas registros onde a instituição tem >= min_pareceres para aquela combinação
    df_filtrado = df_filtrado[df_filtrado['Nº de pareceres'] >= min_pareceres]
    logger.info(f"Registros onde a instituição tem >= {min_pareceres} pareceres: {len(df_filtrado)}")

    # Agrupar por Tecnologia e CID, contar instituições únicas
    tecnologias_validas = df_filtrado.groupby(['Tecnologia', 'CID'])['Órgão de ATS'].nunique()
    # Manter apenas combinações avaliadas por >= 2 instituições
    tecnologias_validas = tecnologias_validas[tecnologias_validas >= 2].index
    logger.info(f"Combinações avaliadas por >= 2 instituições (após filtro de pareceres): {len(tecnologias_validas)}")

    # Filtrar DataFrame
    df_filtrado = df_filtrado.set_index(['Tecnologia', 'CID'])
    df_filtrado = df_filtrado.loc[df_filtrado.index.isin(tecnologias_validas)].reset_index()

    logger.info(f"Registros finais após todos os filtros: {len(df_filtrado)}")

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

    logger.info(f"\nAnálise de diferenças salva: {len(df_difs)} combinações")

    # Estatísticas de diferenças
    dif_100 = df_difs[df_difs['Diferença entre o órgão + favorável e o - favorável'] == 100].shape[0]
    dif_80 = df_difs[df_difs['Diferença entre o órgão + favorável e o - favorável'] >= 80].shape[0]
    dif_50 = df_difs[df_difs['Diferença entre o órgão + favorável e o - favorável'] >= 50].shape[0]
    dif_20 = df_difs[df_difs['Diferença entre o órgão + favorável e o - favorável'] >= 20].shape[0]

    logger.info("\n" + "=" * 60)
    logger.info("ESTATÍSTICAS DE DIVERGÊNCIA ENTRE INSTITUIÇÕES")
    logger.info("=" * 60)
    logger.info(f"Total de combinações analisadas: {len(df_difs)}")
    logger.info(f"Combinações com diferença de 100% (máxima divergência): {dif_100} ({dif_100/len(df_difs)*100:.1f}%)")
    logger.info(f"Combinações com diferença >= 80%: {dif_80} ({dif_80/len(df_difs)*100:.1f}%)")
    logger.info(f"Combinações com diferença >= 50%: {dif_50} ({dif_50/len(df_difs)*100:.1f}%)")
    logger.info(f"Combinações com diferença >= 20%: {dif_20} ({dif_20/len(df_difs)*100:.1f}%)")
    logger.info("=" * 60 + "\n")

    # Análise de concentração de divergências extremas (>= 80%)
    if dif_80 > 0:
        logger.info("\n" + "=" * 60)
        logger.info("CONCENTRAÇÃO DE DIVERGÊNCIAS EXTREMAS (>= 80%)")
        logger.info("=" * 60)

        df_80 = df_difs[df_difs['Diferença entre o órgão + favorável e o - favorável'] >= 80]

        # Contar quantas vezes cada instituição aparece como + favorável
        orgaos_mais_favoraveis = []
        for orgaos_str in df_80['Órgão de ATS + Favorável']:
            # Dividir por "/" quando há empates
            orgaos_list = [org.strip() for org in str(orgaos_str).split('/')]
            orgaos_mais_favoraveis.extend(orgaos_list)

        contagem_mais_fav = pd.Series(orgaos_mais_favoraveis).value_counts()

        logger.info(f"\nInstituições que SEMPRE concedem (>= 80% mais favorável):")
        logger.info(f"Total de casos de divergência >= 80%: {dif_80}")
        for inst, count in contagem_mais_fav.items():
            logger.info(f"  {inst}: {count} casos")

        # Contar quantas vezes cada instituição aparece como - favorável
        orgaos_menos_favoraveis = []
        for orgaos_str in df_80['Órgão de ATS - Favorável']:
            # Dividir por "/" quando há empates
            orgaos_list = [org.strip() for org in str(orgaos_str).split('/')]
            orgaos_menos_favoraveis.extend(orgaos_list)

        contagem_menos_fav = pd.Series(orgaos_menos_favoraveis).value_counts()

        logger.info(f"\nInstituições que NUNCA concedem (>= 80% menos favorável):")
        for inst, count in contagem_menos_fav.items():
            logger.info(f"  {inst}: {count} casos")

        logger.info("\n" + "-" * 60)
        logger.info("INTERPRETAÇÃO:")
        logger.info(f"As divergências extremas (>= 80%) estão concentradas em alguns NatJus específicos.")

        top_favoraveis = contagem_mais_fav.head(3)
        logger.info(f"\nInstituições mais liberais (sempre favoráveis):")
        for inst, count in top_favoraveis.items():
            pct = (count/dif_80)*100
            logger.info(f"  {inst}: {count}/{dif_80} casos ({pct:.1f}%)")

        top_desfavoraveis = contagem_menos_fav.head(3)
        logger.info(f"\nInstituições mais restritivas (sempre desfavoráveis):")
        for inst, count in top_desfavoraveis.items():
            pct = (count/dif_80)*100
            logger.info(f"  {inst}: {count}/{dif_80} casos ({pct:.1f}%)")

        logger.info("\n" + "=" * 60 + "\n")

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

    logger.info(f"\nComparação com Nacional salva: {len(df_comparacao)} registros")

    # Estatísticas
    if not df_comparacao.empty:
        logger.info("\n" + "=" * 60)
        logger.info("COMPARAÇÃO: INSTITUIÇÕES vs NACIONAL")
        logger.info("=" * 60)

        total_comparacoes = len(df_comparacao)
        logger.info(f"Total de comparações realizadas: {total_comparacoes}")

        # Análise de diferenças
        dif_100 = len(df_comparacao[df_comparacao['Ganho'] == 100])
        dif_80 = len(df_comparacao[df_comparacao['Ganho'] >= 80])
        dif_50 = len(df_comparacao[df_comparacao['Ganho'] >= 50])
        dif_20 = len(df_comparacao[df_comparacao['Ganho'] >= 20])

        logger.info(f"\nDIFERENÇAS ENTRE NACIONAL E LOCAIS:")
        logger.info(f"  Diferença de 100%: {dif_100} comparações")
        logger.info(f"  Diferença >= 80%: {dif_80} comparações")
        logger.info(f"  Diferença >= 50%: {dif_50} comparações")
        logger.info(f"  Diferença >= 20%: {dif_20} comparações")

        # Contar em quantos casos é melhor escolher Nacional vs Local
        contagem_melhor = df_comparacao['Melhor'].value_counts()
        casos_nacional = contagem_melhor.get('Nacional', 0)
        casos_local = total_comparacoes - casos_nacional

        logger.info(f"\nESCOLHA ÓTIMA:")
        logger.info(f"  Casos onde NatJus NACIONAL é melhor: {casos_nacional} ({casos_nacional/total_comparacoes*100:.1f}%)")
        logger.info(f"  Casos onde NatJus LOCAL é melhor: {casos_local} ({casos_local/total_comparacoes*100:.1f}%)")

        logger.info(f"\nINTERPRETAÇÃO:")
        logger.info(f"Em {dif_20} casos ({dif_20/total_comparacoes*100:.1f}%), é possível aumentar as chances")
        logger.info(f"de nota técnica favorável em pelo menos 20% pelo mero ato de escolher")
        logger.info(f"entre o NatJus local e o NatJus Nacional.")

        logger.info("\nDistribuição detalhada de casos onde cada instituição teve melhor taxa:")
        for inst, count in contagem_melhor.items():
            pct = count/total_comparacoes*100
            logger.info(f"  {inst}: {count} casos ({pct:.1f}%)")

        # Ganho médio
        ganho_medio = df_comparacao['Ganho'].mean()
        ganho_max = df_comparacao['Ganho'].max()
        logger.info(f"\nGanho médio entre instituições: {ganho_medio:.1f}%")
        logger.info(f"Ganho máximo observado: {ganho_max:.1f}%")
        logger.info("=" * 60 + "\n")

    return df_comparacao


def gerar_tabelas_publicacao(df_maiores_ganhos, pasta_output='outputs'):
    """
    Gera tabelas formatadas para publicação com maiores ganhos.

    Args:
        df_maiores_ganhos (pd.DataFrame): DataFrame com maiores ganhos
        pasta_output (str): Pasta para salvar resultados
    """
    logger.info("\nGerando tabelas formatadas para publicação...")

    # Tabela 2: Maiores aumentos optando pelo NatJus LOCAL
    df_local = df_maiores_ganhos[df_maiores_ganhos['Ganho escolhendo'] != 'Nacional'].copy()

    # Renomear colunas para publicação
    df_local_pub = df_local.rename(columns={
        'Instituição': 'NatJus',
        'Medicamento': 'Princípio ativo',
        'Ganho': 'Aumento'
    })[['NatJus', 'Princípio ativo', 'CID', 'Aumento']]

    # Ordenar por NatJus (para ficar igual ao exemplo fornecido)
    df_local_pub = df_local_pub.sort_values('Aumento', ascending=False)

    salvar_excel(df_local_pub, 'tabela2_maiores_aumentos_natjus_local.xlsx', pasta_output)
    logger.info(f"Tabela 2 (NatJus local) salva: {len(df_local_pub)} registros")

    # Tabela 3: Maiores aumentos optando pelo NatJus NACIONAL
    df_nacional = df_maiores_ganhos[df_maiores_ganhos['Ganho escolhendo'] == 'Nacional'].copy()

    # Renomear colunas para publicação
    df_nacional_pub = df_nacional.rename(columns={
        'Instituição': 'NatJus',
        'Medicamento': 'Princípio ativo',
        'Ganho': 'Aumento'
    })[['NatJus', 'Princípio ativo', 'CID', 'Aumento']]

    # Ordenar por Aumento decrescente
    df_nacional_pub = df_nacional_pub.sort_values('Aumento', ascending=False)

    salvar_excel(df_nacional_pub, 'tabela3_maiores_aumentos_natjus_nacional.xlsx', pasta_output)
    logger.info(f"Tabela 3 (NatJus Nacional) salva: {len(df_nacional_pub)} registros")

    logger.info("\n" + "=" * 60)
    logger.info("RESUMO DAS TABELAS DE PUBLICAÇÃO")
    logger.info("=" * 60)
    logger.info(f"Tabela 2 - Maiores aumentos optando pelo NatJus LOCAL:")
    logger.info(f"  Total de instituições: {len(df_local_pub)}")
    logger.info(f"  Maior aumento: {df_local_pub['Aumento'].max():.1f}%")
    logger.info(f"  Instituições com ganho >= 50%: {len(df_local_pub[df_local_pub['Aumento'] >= 50])}")

    logger.info(f"\nTabela 3 - Maiores aumentos optando pelo NatJus NACIONAL:")
    logger.info(f"  Total de instituições: {len(df_nacional_pub)}")
    logger.info(f"  Maior aumento: {df_nacional_pub['Aumento'].max():.1f}%")
    logger.info(f"  Instituições com ganho >= 50%: {len(df_nacional_pub[df_nacional_pub['Aumento'] >= 50])}")
    logger.info("=" * 60 + "\n")


def analisar_maiores_ganhos(df_comparacao, pasta_output='outputs'):
    """
    Analisa os maiores ganhos por instituição (escolhendo Nacional vs própria instituição).

    Args:
        df_comparacao (pd.DataFrame): DataFrame com comparações
        pasta_output (str): Pasta para salvar resultados
    """
    logger.info("\nAnalisando maiores ganhos por instituição...")

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

    logger.info("\n" + "=" * 60)
    logger.info("MAIORES GANHOS POR INSTITUIÇÃO")
    logger.info("=" * 60)
    logger.info(f"Total de registros de maiores ganhos: {len(df_maiores_ganhos)}")

    # Estatísticas por tipo de escolha
    if not df_maiores_ganhos.empty:
        ganhos_por_escolha = df_maiores_ganhos.groupby('Ganho escolhendo').size()
        logger.info("\nDistribuição de maiores ganhos:")
        for escolha, count in ganhos_por_escolha.items():
            logger.info(f"  Escolhendo {escolha}: {count} casos")

        # Maiores ganhos absolutos
        ganho_max = df_maiores_ganhos['Ganho'].max()
        logger.info(f"\nMaior ganho observado: {ganho_max:.1f}%")

    logger.info("=" * 60 + "\n")

    return df_maiores_ganhos


def gerar_quadro_divergencias_maximas(df_difs, pasta_output='outputs'):
    """
    Gera um quadro formatado com casos de divergência máxima (100%).

    Args:
        df_difs (pd.DataFrame): DataFrame com análise de diferenças
        pasta_output (str): Pasta para salvar resultados

    Returns:
        pd.DataFrame: Quadro formatado com divergências de 100%
    """
    logger.info("\nGerando quadro de divergências máximas (100%)...")

    # Filtrar apenas diferenças de 100%
    df_100 = df_difs[df_difs['Diferença entre o órgão + favorável e o - favorável'] == 100].copy()

    if df_100.empty:
        logger.info("Nenhuma divergência de 100% encontrada.")
        return pd.DataFrame()

    quadro = []

    for _, row in df_100.iterrows():
        # Obter informações
        tecnologia = row['Tecnologia']
        cid = row['CID']
        orgaos_max = row['Órgão de ATS + Favorável']
        valor_max = row['Valor em favorável do Órgão de ATS + favorável']
        orgaos_min = row['Órgão de ATS - Favorável']
        valor_min = row['Valor em favorável do Órgão de ATS - favorável']

        # Determinar quem sempre concede e quem nunca concede
        if valor_max == 100 and valor_min == 0:
            sempre_concede = orgaos_max
            nunca_concede = orgaos_min
        else:
            # Caso não seja exatamente 100% vs 0%, ainda mostra
            sempre_concede = f"{orgaos_max} ({valor_max:.0f}%)"
            nunca_concede = f"{orgaos_min} ({valor_min:.0f}%)"

        quadro.append({
            'Princípio ativo': tecnologia,
            'CID': cid,
            'Sempre concede(m)': sempre_concede,
            'Nunca concede(m)': nunca_concede
        })

    df_quadro = pd.DataFrame(quadro)
    salvar_excel(df_quadro, 'quadro_divergencias_maximas.xlsx', pasta_output)

    logger.info(f"Quadro de divergências máximas salvo: {len(df_quadro)} casos")

    return df_quadro


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

    # Gerar quadro de divergências máximas
    gerar_quadro_divergencias_maximas(df_difs, pasta_output)

    # Comparação com Nacional
    df_comparacao = comparar_com_nacional(df_base, pasta_output)

    # Analisar maiores ganhos
    if not df_comparacao.empty:
        df_maiores_ganhos = analisar_maiores_ganhos(df_comparacao, pasta_output)

        # Gerar tabelas formatadas para publicação
        gerar_tabelas_publicacao(df_maiores_ganhos, pasta_output)

    logger.info("=" * 60)
    logger.info("ANÁLISE DE DIFERENÇAS POR MEDICAMENTOS CONCLUÍDA")
    logger.info(f"Resultados salvos em: {pasta_output}/")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
