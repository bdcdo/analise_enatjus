"""
Script de filtragem e agregação da base E-NatJus.

Este script:
1. Carrega a base bruta
2. Filtra por data (até 30/06/2025)
3. Filtra por tipo de tecnologia (medicamentos)
4. Agrega instituições conforme descrito na metodologia
5. Salva a base processada
"""

import polars as pl

print("=" * 80)
print("INICIANDO PROCESSAMENTO DA BASE E-NATJUS")
print("=" * 80)

# 1. Carregar base bruta
print("\n[1/5] Carregando base bruta...")
df = pl.read_parquet('base_enatjus.parquet')
print(f"   ✓ Registros carregados: {len(df):,}")

# 2. Processar data e filtrar
print("\n[2/5] Convertendo datas e filtrando até 31/12/2025...")
df = df.with_columns(
    pl.col("data_emissao")
      .str.strptime(pl.Datetime, format="%d/%m/%Y %H:%M:%S", strict=False)
)

df_filtrado = df.filter(
    pl.col("data_emissao") <= pl.datetime(2024, 12, 31, 23, 59, 59)
)
print(f"   ✓ Registros após filtro de data: {len(df_filtrado):,}")
print(f"   ✓ Registros removidos: {len(df) - len(df_filtrado):,}")

# 3. Filtrar por tipo de tecnologia (medicamentos)
print("\n[3/5] Filtrando por tipo de tecnologia (medicamentos)...")
df_filtrado = df_filtrado.filter(
    pl.col('selTipoTecnologia') == '1'
)
print(f"   ✓ Registros após filtro de tecnologia: {len(df_filtrado):,}")

# 4. Agregar instituições
print("\n[4/5] Agregando instituições conforme metodologia...")
print("   • Paraná: CAMS/TJPR, CHR, UEL, UFPR → PR")
print("   • Amazonas: SES, SEMSA → AM")
print("   • São Paulo: Hospital das Clínicas → SP")
print("   • RS não identificado → NÃO_PREENCHIDO")

df_filtrado = df_filtrado.with_columns(
    pl.when(pl.col("origem_tratada").is_in(["PR/CAMS", "PR/CHR", "PR/UEL", "PR/CHC-UFPR"]))
      .then(pl.lit("PR"))
    .when(pl.col("origem_tratada").is_in(["AM/SES", "AM/SEMSA", "AM"]))
      .then(pl.lit("AM"))
    .when(pl.col("origem_tratada") == "SP/HC")
      .then(pl.lit("SP"))
      .when(pl.col("origem_tratada") == "DF")
      .then(pl.lit("DFT"))
    .when(pl.col("origem_tratada").is_in(["RS", "Não informada"]))
      .then(pl.lit("NÃO_PREENCHIDO"))
    .otherwise(pl.col("origem_tratada"))
    .alias("origem_tratada")
)

print(f"   ✓ Total de registros mantidos: {len(df_filtrado):,}")

# Mostrar contagem por instituição após agregação
print("\n   Distribuição após agregação:")
contagem = df_filtrado['origem_tratada'].value_counts(sort=True)
for row in contagem.iter_rows():
    inst, count = row
    print(f"      {inst:30s}: {count:>6,}")

# 6. Salvar base processada
print("\n[5/5] Salvando base processada...")
df_filtrado.write_parquet('base_enatjus_2025-1.parquet', compression='zstd', compression_level=6)
print(f"   ✓ Arquivo salvo: base_enatjus_2025-1.parquet")

print("\n" + "=" * 80)
print("PROCESSAMENTO CONCLUÍDO COM SUCESSO")
print("=" * 80)
print(f"\nResumo:")
print(f"  - Registros iniciais: {len(df):,}")
print(f"  - Registros finais: {len(df_filtrado):,}")
print(f"  - Redução: {len(df) - len(df_filtrado):,} ({(1 - len(df_filtrado)/len(df))*100:.1f}%)")
