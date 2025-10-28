"""
Módulo de utilidades compartilhadas para análises E-NatJus.

Este módulo contém funções reutilizáveis para processamento de dados,
cálculos estatísticos e visualizações utilizadas em múltiplas análises.
"""

import pandas as pd
import math
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import logging
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# MAPEAMENTO DE COLUNAS E VALORES
# ============================================================================

# Mapeamento de valores codificados para texto
MAPA_VALORES = {
    'selConclusao': {
        'F': 'Favorável',
        'N': 'Não favorável',
        'NÃO_PREENCHIDO': 'Não preenchido'
    },
    'selDefensoriaPublica': {
        'D': 'Defensoria Pública',
        'M': 'Ministério Público',
        'NÃO_PREENCHIDO': 'Não preenchido'
    },
    'selEsfera': {
        'E': 'Justiça Estadual',
        'F': 'Justiça Federal',
        'NÃO_PREENCHIDO': 'Não preenchido'
    },
    'selStaGenero': {
        'M': 'Masculino',
        'F': 'Feminino',
        'NÃO_PREENCHIDO': 'Não preenchido'
    },
    'selRecomendacaoConitec': {
        'F': 'Recomendada (Favorável)',
        'D': 'Não Recomendada (Desfavorável)',
        'V': 'Não avaliada',
        'NÃO_PREENCHIDO': 'Não preenchido'
    },
    'binarios': {  # Para colunas S/N
        'S': 'Sim',
        'N': 'Não',
        'X': 'Parcial',
        'B': 'Ambos',
        'NÃO_APLICÁVEL': 'Não aplicável',
        'NÃO_PREENCHIDO': 'Não preenchido'
    }
}


def decodificar_coluna(df, coluna, mapa_nome='binarios'):
    """
    Decodifica uma coluna com valores codificados.

    Args:
        df (pd.DataFrame): DataFrame
        coluna (str): Nome da coluna
        mapa_nome (str): Nome do mapeamento a usar (padrão: 'binarios')

    Returns:
        pd.Series: Coluna decodificada
    """
    if mapa_nome in MAPA_VALORES:
        return df[coluna].map(MAPA_VALORES[mapa_nome])
    return df[coluna]


# ============================================================================
# MAPEAMENTO DE CID
# ============================================================================

# Dicionário com o mapeamento de códigos CID para grupos de doenças
MAPA_CID = {
    ('A', 'B'): 'Algumas doenças infecciosas e parasitárias (A00-B99)',
    ('C', 'C'): 'Neoplasias (tumores) (C00-C97)',
    ('D', 'D48'): 'Neoplasias (tumores) (D00-D48)',
    ('D49', 'D89'): 'Doenças do sangue e dos órgãos hematopoéticos e alguns transtornos envolvendo o sistema imunológico (D50-D89)',
    ('E', 'E'): 'Doenças endócrinas, nutricionais e metabólicas (E00-E90)',
    ('F', 'F'): 'Transtornos mentais e comportamentais (F00-F99)',
    ('G', 'G'): 'Doenças do sistema nervoso (G00-G99)',
    ('H00', 'H59'): 'Doenças do olho e anexos (H00-H59)',
    ('H60', 'H95'): 'Doenças do ouvido e da apófise mastoide (H60-H95)',
    ('I', 'I'): 'Doenças do sistema circulatório (I00-I99)',
    ('J', 'J'): 'Doenças do sistema respiratório (J00-J99)',
    ('K', 'K'): 'Doenças do sistema digestivo (K00-K93)',
    ('L', 'L'): 'Doenças da pele e do tecido subcutâneo (L00-L99)',
    ('M', 'M'): 'Doenças do sistema osteomuscular e do tecido conjuntivo (M00-M99)',
    ('N', 'N'): 'Doenças do sistema geniturinário (N00-N99)',
    ('O', 'O'): 'Gravidez, parto e o puerpério (O00-O99)',
    ('P', 'P'): 'Algumas afecções originadas no período perinatal (P00-P96)',
    ('Q', 'Q'): 'Malformações congênitas, deformidades e anomalias cromossômicas (Q00-Q99)',
    ('R', 'R'): 'Sintomas, sinais e achados anormais de exames clínicos e de laboratório, não classificados em outra parte (R00-R99)',
    ('S', 'T'): 'Lesões, envenenamentos e algumas outras consequências de causas externas (S00-T98)',
    ('U', 'U'): 'Códigos para propósitos especiais (U00-U99)',
    ('V', 'Y'): 'Códigos de causas externas de morbidade e de mortalidade (V01-Y98)',
    ('Z', 'Z'): 'Fatores que influenciam o estado de saúde e o contato com os serviços de saúde (Z00-Z99)',
}


def obter_tipo_do_cid(linha):
    """
    Obtém o tipo/grupo de doença a partir do código CID.

    Args:
        linha (pd.Series): Linha do DataFrame com colunas 'CID4-Letra' e 'CID4-Num'

    Returns:
        str: Descrição do grupo de doenças ou string vazia se não encontrado
    """
    letra = linha['CID4-Letra']
    num_str = linha['CID4-Num']

    if pd.isna(num_str):
        return ''

    # Convertendo para inteiro para comparação
    try:
        num = int(num_str)
    except:
        return ''

    # Casos especiais
    if letra == 'H':
        if num <= 59:
            return 'Doenças do olho e anexos (H00-H59)'
        else:
            return 'Doenças do ouvido e da apófise mastoide (H60-H95)'
    elif letra == 'D':
        if num <= 48:
            return 'Neoplasias (tumores) (D00-D48)'
        else:
            return 'Doenças do sangue e dos órgãos hematopoéticos e alguns transtornos envolvendo o sistema imunológico (D50-D89)'

    # Casos gerais
    for key, value in MAPA_CID.items():
        # Verifica se a letra está no intervalo
        if letra >= key[0] and letra <= key[1]:
            # Para chaves simples como ('A', 'B')
            if isinstance(key[0], str) and len(key[0]) == 1 and isinstance(key[1], str) and len(key[1]) == 1:
                return value

    return ''


# ============================================================================
# CÁLCULOS ESTATÍSTICOS
# ============================================================================

def intervalo_confianca_proporcao(p, n, z=1.96):
    """
    Calcula o intervalo de confiança para uma proporção.

    Args:
        p (float): Proporção observada (ex: 0.8 para 80%)
        n (int): Número total de respostas
        z (float): Valor crítico para o nível de confiança (default 1.96 para 95%)

    Returns:
        tuple: (limite_inferior, limite_superior) do intervalo de confiança
    """
    if n > 0:
        erro_padrao = math.sqrt((p * (1 - p)) / n)
        margem_erro = z * erro_padrao
        limite_inferior = p - margem_erro
        limite_superior = p + margem_erro
    else:
        limite_inferior = 0
        limite_superior = 0

    return limite_inferior, limite_superior


def processar_subconjunto(df, coluna, valor_filtro, min_observacoes, geral=False):
    """
    Processa um subconjunto de dados para análise de pareceres por instituição.

    Args:
        df (pd.DataFrame): DataFrame com os dados dos pareceres
        coluna (str): Nome da coluna para filtrar os dados
        valor_filtro: Valor específico para filtrar na coluna
        min_observacoes (int): Número mínimo de observações para incluir uma instituição
        geral (bool): Se True, analisa todos os dados sem filtrar por coluna

    Returns:
        list: Lista de dicionários com os resultados da análise
    """
    resultados = []

    for inst in df['origem_tratada'].unique():
        if geral:
            subset = df[df['origem_tratada'] == inst]
        else:
            subset = df[(df['origem_tratada'] == inst) & (df[coluna] == valor_filtro)]

        qtd_total = len(subset)

        if qtd_total >= min_observacoes:
            inst_nome = inst
            # selConclusao: 'F' = Favorável
            favoravel_count = subset[subset['selConclusao'] == 'F'].shape[0]
            proporcao_favoravel = favoravel_count / qtd_total if qtd_total > 0 else 0

            limite_inferior, limite_superior = intervalo_confianca_proporcao(proporcao_favoravel, qtd_total)

            resultados.append({
                'Coluna': 'Geral' if geral else coluna,
                'Órgão de ATS': inst_nome,
                'Nº de pareceres': qtd_total,
                'Proporção Favorável': proporcao_favoravel,
                'IC Inferior': limite_inferior,
                'IC Superior': limite_superior
            })

    return resultados


# ============================================================================
# VISUALIZAÇÕES
# ============================================================================

# Cores para os órgãos (usado em gráficos)
cmap = cm.get_cmap('tab20', 20)

CORES_ORGAO = {
    'Nacional': cmap(0),
    'RS/DMJ': cmap(2),
    'BA': cmap(4),
    'MS': cmap(6),
    'SP': cmap(8),
    'MT': cmap(10),
    'PR': cmap(12),
    'TelessaúdeRS-UFRGS': cmap(14),
    'MA': cmap(16),
    'DF': cmap(18),
    'ES': cmap(1),
    'RJ': cmap(3),
    'PE': cmap(5),
    'SE': cmap(7),
    'RN': cmap(9),
    'GO': cmap(11),
    'RR': cmap(13),
    'TO': cmap(15),
    'AL': cmap(17),
    'Outros': cmap(19)
}


def obter_cor(orgao):
    """
    Retorna a cor associada a um órgão para uso em gráficos.

    Args:
        orgao (str): Nome do órgão

    Returns:
        tuple: Cor RGB para o órgão
    """
    return CORES_ORGAO.get(orgao, (0, 0, 0))  # Preto como padrão


def grafico_barras_sucesso(df_sucesso, x=12, y=7, z=300, output_path=None):
    """
    Cria gráfico de barras com taxas de sucesso por instituição.

    Args:
        df_sucesso (pd.DataFrame): DataFrame com colunas 'Órgão de ATS' e 'Proporção Favorável'
        x (int): Largura da figura
        y (int): Altura da figura
        z (int): DPI da figura
        output_path (str): Caminho para salvar o gráfico (opcional)
    """
    # Ordenar o DataFrame pela coluna 'Proporção Favorável' em ordem ascendente
    df_sucesso = df_sucesso.sort_values(by='Proporção Favorável')

    plt.rcParams.update({'font.size': 16.5})
    plt.figure(figsize=(x, y), dpi=z)
    bars = plt.bar(
        df_sucesso['Órgão de ATS'],
        df_sucesso['Proporção Favorável'] * 100,
        capsize=5
    )
    plt.ylim(0, 100)
    plt.xticks(rotation=45, ha='right', fontsize=22)
    plt.tight_layout()
    plt.xlim(-0.5, len(df_sucesso['Órgão de ATS']) - 0.5)
    plt.yticks(range(0, 110, 20))

    # Adicionar os valores exatos acima de cada barra
    for bar in bars:
        yval = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width()/2, yval, round(yval, 1),
            ha='center', va='bottom'
        )

    if output_path:
        plt.savefig(output_path, bbox_inches='tight')
        logger.info(f"Gráfico salvo em: {output_path}")

    plt.close()


# ============================================================================
# PROCESSAMENTO DE DADOS
# ============================================================================

def processar_cid(df):
    """
    Processa colunas de CID, extraindo componentes e classificando por tipo.

    Args:
        df (pd.DataFrame): DataFrame com coluna 'txtCid'

    Returns:
        pd.DataFrame: DataFrame com colunas CID processadas adicionadas
    """
    df = df.copy()

    # Extrair componentes do CID
    df['CID2'] = df['txtCid'].str.split(' - ').str[0]
    df['CID3'] = df['CID2'].str.split('.').str[0]
    df['CID4-Letra'] = df['CID3'].str.extract('(\D)', expand=False)
    df['CID4-Num'] = df['CID3'].str.extract('(\d+)', expand=False)

    # Aplicar classificação por tipo
    df['CID4-Tipo'] = df.apply(obter_tipo_do_cid, axis=1)

    logger.info("Processamento de CID concluído")
    return df


def carregar_base_enatjus(caminho='base_enatjus_2025-1.parquet'):
    """
    Carrega a base de dados E-NatJus a partir do arquivo parquet.

    Args:
        caminho (str): Caminho para o arquivo parquet (padrão: 'base_enatjus_2025-1.parquet')

    Returns:
        pd.DataFrame: DataFrame com os dados carregados
    """
    try:
        logger.info(f"Carregando base de dados: {caminho}")
        df = pd.read_parquet(caminho)
        logger.info(f"Base carregada com sucesso: {len(df)} registros")
        return df
    except Exception as e:
        logger.error(f"Erro ao carregar base de dados: {e}")
        raise


def criar_pasta_outputs(caminho='outputs'):
    """
    Cria pasta de outputs se não existir.

    Args:
        caminho (str): Caminho da pasta
    """
    if not os.path.exists(caminho):
        os.makedirs(caminho)
        logger.info(f"Pasta criada: {caminho}")


def salvar_excel(df, nome_arquivo, pasta='outputs'):
    """
    Salva DataFrame em arquivo Excel na pasta de outputs.

    Args:
        df (pd.DataFrame): DataFrame a salvar
        nome_arquivo (str): Nome do arquivo
        pasta (str): Pasta de destino
    """
    criar_pasta_outputs(pasta)
    caminho_completo = os.path.join(pasta, nome_arquivo)
    df.to_excel(caminho_completo, index=False)
    logger.info(f"Arquivo salvo: {caminho_completo}")
