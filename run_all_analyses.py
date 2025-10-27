#!/usr/bin/env python3
"""
Script master para executar todas as análises E-NatJus sequencialmente.

Este script executa todos os scripts de análise na ordem correta,
conforme definido no README.md, capturando logs e tratando erros.
"""

import subprocess
import sys
import os
import time
from datetime import datetime
import logging

# Configurar logging
log_filename = f"execucao_completa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# Definir scripts na ordem de execução
SCRIPTS = [
    {
        'path': '0 Descritivos gerais/analise_pedidos.py',
        'descricao': 'Análise de pedidos por CID e princípios ativos'
    },
    {
        'path': '0 Descritivos gerais/analise_geral.py',
        'descricao': 'Descritivos gerais por instituição'
    },
    {
        'path': '1 Adesao/analise_adesao.py',
        'descricao': 'Análise temporal de adesão'
    },
    {
        'path': '2 Divergencia geral/analise_diferencas_regionais.py',
        'descricao': 'Análise de divergências regionais'
    },
    {
        'path': '3 Divergencia por medicamentos/gerar_base_diferencas_medicamentos.py',
        'descricao': 'Geração de base de controle por medicamento'
    },
    {
        'path': '3 Divergencia por medicamentos/analise_diferencas_medicamentos.py',
        'descricao': 'Análise de divergências por medicamento'
    }
]


def verificar_ambiente_virtual():
    """
    Verifica se o script está sendo executado em um ambiente virtual.

    Returns:
        bool: True se estiver em ambiente virtual, False caso contrário
    """
    # Verifica se está em ambiente virtual
    em_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

    if em_venv:
        logger.info("✓ Executando em ambiente virtual")
        logger.info(f"  Python: {sys.executable}")
        return True
    else:
        logger.warning("⚠ AVISO: Não está executando em ambiente virtual")
        logger.warning(f"  Python: {sys.executable}")
        return False


def verificar_base_dados():
    """
    Verifica se a base de dados principal existe.

    Returns:
        bool: True se a base existe, False caso contrário
    """
    base_path = 'base_enatjus_2025-1.parquet'

    if os.path.exists(base_path):
        size_mb = os.path.getsize(base_path) / (1024 * 1024)
        logger.info(f"✓ Base de dados encontrada: {base_path} ({size_mb:.1f} MB)")
        return True
    else:
        logger.error(f"✗ Base de dados NÃO encontrada: {base_path}")
        return False


def executar_script(script_info, numero, total):
    """
    Executa um script Python e captura sua saída.

    Args:
        script_info (dict): Dicionário com informações do script
        numero (int): Número do script atual
        total (int): Total de scripts

    Returns:
        bool: True se execução foi bem-sucedida, False caso contrário
    """
    script_path = script_info['path']
    descricao = script_info['descricao']

    logger.info("")
    logger.info("=" * 80)
    logger.info(f"[{numero}/{total}] {descricao}")
    logger.info(f"Script: {script_path}")
    logger.info("=" * 80)

    # Verificar se o script existe
    if not os.path.exists(script_path):
        logger.error(f"✗ Script não encontrado: {script_path}")
        return False

    # Separar diretório e nome do arquivo
    script_dir = os.path.dirname(script_path)
    script_name = os.path.basename(script_path)

    # Executar o script
    inicio = time.time()

    try:
        # Usar python3 conforme instrução do usuário para Linux
        # Executar a partir do diretório do script para manter compatibilidade
        # com caminhos relativos (../ para acessar base_enatjus_2025-1.parquet)
        resultado = subprocess.run(
            ['python3', script_name],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            cwd=script_dir if script_dir else '.'
        )

        fim = time.time()
        duracao = fim - inicio

        # Exibir saída do script
        if resultado.stdout:
            logger.info("Saída:")
            for linha in resultado.stdout.splitlines():
                logger.info(f"  {linha}")

        if resultado.stderr and resultado.returncode != 0:
            logger.error("Erros:")
            for linha in resultado.stderr.splitlines():
                logger.error(f"  {linha}")

        # Verificar código de retorno
        if resultado.returncode == 0:
            logger.info(f"✓ Script executado com sucesso em {duracao:.1f}s")
            return True
        else:
            logger.error(f"✗ Script falhou com código {resultado.returncode} após {duracao:.1f}s")
            return False

    except Exception as e:
        fim = time.time()
        duracao = fim - inicio
        logger.error(f"✗ Erro ao executar script após {duracao:.1f}s: {e}")
        return False


def main():
    """
    Função principal que coordena a execução de todos os scripts.
    """
    logger.info("╔" + "═" * 78 + "╗")
    logger.info("║" + " " * 20 + "EXECUÇÃO COMPLETA DAS ANÁLISES E-NATJUS" + " " * 19 + "║")
    logger.info("╚" + "═" * 78 + "╝")
    logger.info("")
    logger.info(f"Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Total de scripts: {len(SCRIPTS)}")
    logger.info(f"Log sendo salvo em: {log_filename}")
    logger.info("")

    # Verificações iniciais
    logger.info("📋 VERIFICAÇÕES INICIAIS")
    logger.info("-" * 80)

    verificar_ambiente_virtual()

    if not verificar_base_dados():
        logger.error("")
        logger.error("ERRO: Base de dados não encontrada. Abortando execução.")
        sys.exit(1)

    logger.info("")

    # Executar scripts
    inicio_total = time.time()
    scripts_sucesso = 0
    scripts_falha = 0

    for i, script_info in enumerate(SCRIPTS, 1):
        sucesso = executar_script(script_info, i, len(SCRIPTS))

        if sucesso:
            scripts_sucesso += 1
        else:
            scripts_falha += 1
            logger.error("")
            logger.error("!" * 80)
            logger.error("ERRO: Script falhou. Abortando execução dos scripts restantes.")
            logger.error("!" * 80)
            break

    # Resumo final
    fim_total = time.time()
    duracao_total = fim_total - inicio_total

    logger.info("")
    logger.info("╔" + "═" * 78 + "╗")
    logger.info("║" + " " * 30 + "RESUMO FINAL" + " " * 36 + "║")
    logger.info("╚" + "═" * 78 + "╝")
    logger.info("")
    logger.info(f"Fim: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Duração total: {duracao_total/60:.1f} minutos ({duracao_total:.1f}s)")
    logger.info("")
    logger.info(f"Scripts executados com sucesso: {scripts_sucesso}/{len(SCRIPTS)}")
    logger.info(f"Scripts com falha: {scripts_falha}/{len(SCRIPTS)}")
    logger.info("")
    logger.info(f"Log completo salvo em: {log_filename}")

    if scripts_falha > 0:
        logger.error("")
        logger.error("⚠ ATENÇÃO: Alguns scripts falharam. Verifique o log acima.")
        sys.exit(1)
    else:
        logger.info("")
        logger.info("✓ Todas as análises foram executadas com sucesso!")
        sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("")
        logger.warning("⚠ Execução interrompida pelo usuário (Ctrl+C)")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"✗ Erro inesperado: {e}")
        sys.exit(1)
