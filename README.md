# Análises E-NatJus - Projeto de Mestrado

Projeto de análise de dados do sistema E-NatJus, contendo scripts Python para análises descritivas, temporais e comparativas de pareceres técnicos emitidos por diferentes instituições.

## 📋 Estrutura do Projeto

```
48_mestrado_publi1/
├── README.md                          # Este arquivo
├── run_all_analyses.py                # Script master para executar todas análises
├── utils.py                           # Funções compartilhadas
├── base_enatjus_2025-1.parquet       # Base de dados principal
│
├── 0 Descritivos gerais/
│   ├── analise_pedidos.py            # Análise de pedidos por CID e princípios ativos
│   ├── analise_geral.py              # Descritivos gerais por instituição
│   └── outputs/                       # Resultados das análises
│
├── 1 Adesao/
│   ├── analise_adesao.py             # Análise temporal de adesão
│   └── outputs/                       # Gráficos e tabelas
│
├── 2 Divergencia geral/
│   ├── analise_diferencas_regionais.py  # Taxas de concessão por instituição
│   └── outputs/                       # Resultados e gráficos
│
└── 3 Divergencia por medicamentos/
    ├── gerar_base_diferencas_medicamentos.py  # Gera base de controle
    ├── analise_diferencas_medicamentos.py     # Analisa divergências
    └── outputs/                       # Resultados das análises
```

## 🔧 Configuração do Ambiente

### Pré-requisitos

- Python 3.11+
- `uv` (gerenciador de pacotes)
- Ambiente virtual configurado

### Instalação de Dependências

```bash
# Instalar dependências necessárias
uv pip install pandas pyarrow matplotlib openpyxl unidecode
```

## 📊 Descrição dos Scripts

### `utils.py` - Módulo de Utilidades

Contém funções compartilhadas utilizadas por todos os scripts:

- **Mapeamento de CID**: Classificação de códigos CID em grupos de doenças
- **Cálculos estatísticos**: Intervalos de confiança, processamento de subconjuntos
- **Visualizações**: Cores para gráficos, funções de plotagem
- **Processamento de dados**: Carregamento de base, processamento de CID, salvamento de resultados

### Pasta: `0 Descritivos gerais/`

#### `analise_pedidos.py`

Analisa a distribuição de pedidos de pareceres técnicos.

**Análises realizadas:**
- Grupos de doenças (CID) por instituição (Nacional vs Outros)
- Top 10 CIDs específicos mais comuns
- Top 10 princípios ativos mais solicitados com CID principal

**Saídas:**
- `grupoD_outros.xlsx` - Grupos de doenças (instituições exceto Nacional)
- `grupoD_nacional.xlsx` - Grupos de doenças (Nacional)
- `doencas_outros.xlsx` - Top 10 CIDs (outros)
- `doencas_nacional.xlsx` - Top 10 CIDs (Nacional)
- `principio_outros.xlsx` - Top 10 princípios ativos (outros)
- `principio_nacional.xlsx` - Top 10 princípios ativos (Nacional)

**Execução:**
```bash
cd "0 Descritivos gerais"
python3 analise_pedidos.py
```

#### `analise_geral.py`

Gera estatísticas descritivas agregadas para instituições com ≥100 pareceres.

**Análises realizadas:**
- Proporções de características por instituição (gênero, defensoria, esfera, etc.)
- Taxas de conclusão favorável
- Características dos demandantes

**Saídas:**
- `df_descGeral.xlsx` - Descritivos gerais completos
- `demandantes.xlsx` - Foco em características dos demandantes

**Execução:**
```bash
cd "0 Descritivos gerais"
python3 analise_geral.py
```

### Pasta: `1 Adesao/`

#### `analise_adesao.py`

Analisa a evolução temporal da adesão das instituições ao E-NatJus.

**Análises realizadas:**
- Proporção de pareceres urgentes por instituição
- Evolução temporal de adesão (acumulado, média móvel, stackplot)
- Distribuição anual de pareceres

**Saídas:**
- `analise_urgencia_instituicoes.xlsx` - Análise de urgência
- `total_adesao.xlsx` - Tabela de adesão anual
- `grafico_acumulado_sem_nacional.png` - Gráfico acumulado
- `grafico_media_movel.png` - Média móvel de 12 meses
- `grafico_stackplot.png` - Distribuição anual empilhada

**Execução:**
```bash
cd "1 Adesao"
python3 analise_adesao.py
```

### Pasta: `2 Divergencia geral/`

#### `analise_diferencas_regionais.py`

Analisa divergências regionais nas taxas de concessão de pareceres.

**Análises realizadas:**
- Taxas de concessão geral por instituição
- Taxas por subconjuntos:
  - Uso offlabel (não conforme indicação)
  - Não previsto em PCDT
  - Não incorporado ao SUS
  - Não recomendado pela CONITEC

**Saídas:**
- `taxas_concessao.xlsx` - Taxas gerais com intervalos de confiança
- `taxas_concessao_subconjuntos.xlsx` - Taxas por subconjunto
- `grafico_taxas_gerais.png` - Gráfico de barras geral
- `grafico_[subconjunto].png` - Gráficos por subconjunto

**Execução:**
```bash
cd "2 Divergencia geral"
python3 analise_diferencas_regionais.py
```

### Pasta: `3 Divergencia por medicamentos/`

#### `gerar_base_diferencas_medicamentos.py`

Gera base de controle para análise de divergências por medicamento específico.

**Processamento:**
1. Extrai CID simplificado (ex: A00, B12)
2. Padroniza nomes de medicamentos (remove espaços, acentos, minúsculas)
3. Filtra combinações medicamento+CID com ≥10 observações
4. Agrega dados por instituição, medicamento e CID

**Saídas:**
- `controle_por_tratamento_e_por_CID.xlsx` - Base de controle
- `exemplo_base.xlsx` - Exemplo das primeiras 30 linhas

**Execução:**
```bash
cd "3 Divergencia por medicamentos"
python3 gerar_base_diferencas_medicamentos.py
```

#### `analise_diferencas_medicamentos.py`

Analisa divergências entre instituições para medicamentos específicos.

**Análises realizadas:**
- Identificação de combinações medicamento+CID avaliadas por ≥2 instituições
- Diferenças entre instituições mais e menos favoráveis
- Comparação de cada instituição com a Nacional
- Maiores ganhos potenciais por escolha de instituição

**Saídas:**
- `diferencas_medicamentos.xlsx` - Análise de diferenças
- `comparacao_instituicoes_nacional.xlsx` - Comparação com Nacional
- `maiores_ganhos_instituicoes_e_nacional.xlsx` - Análise de ganhos

**Execução:**
```bash
cd "3 Divergencia por medicamentos"
python3 analise_diferencas_medicamentos.py
```

**⚠️ Observação:** Este script deve ser executado **após** `gerar_base_diferencas_medicamentos.py`

## 🗂️ Estrutura da Base de Dados

A base `base_enatjus_2025-1.parquet` contém 308.315 registros com 73 colunas, incluindo:

### Colunas Principais

- **Identificação**: `idNotaTecnica`, `arquivo`, `status`
- **Instituição**: `origem_tratada` (coluna utilizada para agregações)
- **Paciente**: `txtIdade`, `selStaGenero`, `txtCidade`
- **Processo**: `selDefensoriaPublica`, `selEsfera`, `txtServentia`
- **Diagnóstico**: `txtCid`, `txtDescAvaliacaoDiagnosticoSemCID`
- **Tecnologia**: `txtDcb` (princípio ativo), `txtDcbComercial`, `selRegistroAnvisa`
- **Características**: `selUsoContinuo`, `selIndicacaoConformidade`, `selPrevistoProtocolo`
- **Disponibilidade**: `selDisponivelSus`, `selOncologico`, `selExisteGenerico`
- **Evidências**: `selRecomendacaoConitec`, `selEvidenciaCientifica`
- **Conclusão**: `selConclusao`, `selAlegacaoUrgencia`, `selApoioTutoria`
- **Temporal**: `data_emissao`

### Mapeamento de Valores Codificados

- **selConclusao**: `F` = Favorável, `N` = Não favorável
- **selStaGenero**: `F` = Feminino, `M` = Masculino
- **selDefensoriaPublica**: `D` = Defensoria Pública, `M` = Ministério Público
- **selEsfera**: `E` = Estadual, `F` = Federal
- **selRecomendacaoConitec**: `F` = Não Recomendada, `V` = Recomendada, `D` = Sem recomendação
- **Campos binários**: `S` = Sim, `N` = Não, `X` = Parcial, `NÃO_APLICÁVEL`, `NÃO_PREENCHIDO`

## 📈 Fluxo de Execução Recomendado

### Execução Automatizada (Recomendado)

Para executar todas as análises automaticamente em sequência:

```bash
python3 run_all_analyses.py
```

Este script master:
- ✓ Verifica se você está em ambiente virtual
- ✓ Verifica se a base de dados existe
- ✓ Executa todos os scripts na ordem correta
- ✓ Captura e exibe logs de cada execução
- ✓ Para a execução em caso de erro
- ✓ Gera log consolidado com timestamp
- ✓ Exibe resumo final com tempo de execução

### Execução Manual

Se preferir executar os scripts individualmente:

```bash
# 1. Análises descritivas gerais
cd "0 Descritivos gerais"
python3 analise_pedidos.py
python3 analise_geral.py
cd ..

# 2. Análise de adesão temporal
cd "1 Adesao"
python3 analise_adesao.py
cd ..

# 3. Análise de divergências regionais
cd "2 Divergencia geral"
python3 analise_diferencas_regionais.py
cd ..

# 4. Análise de divergências por medicamentos
cd "3 Divergencia por medicamentos"
python3 gerar_base_diferencas_medicamentos.py
python3 analise_diferencas_medicamentos.py
cd ..
```

## 📝 Observações Importantes

1. **Coluna de Instituição**: Todos os scripts utilizam a coluna `origem_tratada` para identificar a instituição responsável

2. **Filtros Aplicados**:
   - Maioria das análises filtra apenas conclusões "Favorável" (F) e "Não favorável" (N)
   - Análises excluem registros com `origem_tratada = 'NÃO_PREENCHIDO'`

3. **Instituição "Nacional"**:
   - Corresponde ao Hospital Israelita Albert Einstein
   - É frequentemente analisada separadamente das demais instituições

4. **Saídas**:
   - Todos os arquivos Excel e gráficos são salvos na pasta `outputs/` de cada diretório
   - As pastas `outputs/` são criadas automaticamente se não existirem

5. **Logging**:
   - Todos os scripts geram logs informativos durante a execução
   - Os logs incluem contagens de registros, instituições analisadas e arquivos gerados

## 🐛 Solução de Problemas

### Erro de módulo não encontrado

```bash
# Instalar dependências faltantes
uv pip install [nome_do_modulo]
```

### Erro ao carregar arquivo parquet

```bash
# Verificar se pyarrow está instalado
uv pip install pyarrow
```

### Erro "No such file or directory"

```bash
# Certifique-se de estar no diretório correto
cd "nome_da_pasta"
python3 nome_do_script.py
```

## 👥 Autores

Projeto de Mestrado - Análise de Dados E-NatJus

## 📄 Licença

[Especificar licença se aplicável]

## 🔄 Histórico de Versões

- **v1.1** (2025-01) - Adição de script master de execução
  - Criação do `run_all_analyses.py` para execução automatizada
  - Execução sequencial de todos os scripts em ordem
  - Logs consolidados com timestamp
  - Verificações de ambiente e base de dados

- **v1.0** (2025-01) - Conversão inicial de notebooks para scripts Python
  - Implementação de logging
  - Documentação completa com docstrings
  - Organização em estrutura modular
  - Utilização da base atualizada (base_enatjus_2025-1.parquet)
