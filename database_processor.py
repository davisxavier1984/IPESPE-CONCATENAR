import sqlite3
import pandas as pd
from typing import Generator, Tuple, List, Dict
import tempfile
import os
import re


# Schema gabarito (fonte da verdade) para ordenação das colunas
TEMPLATE_SCHEMA = [
    "ID Coleta", "ID Questionário", "Autor", "Data início", "Data fim", "Duração", 
    "Latitude", "Longitude", "Revisão", "Sincronizacao", "Finalizada", "PIN", 
    "Enviada para Webhook", "Número do WhatsApp", "ramal", "P1", "P2", "P3", "P4", 
    "P5", "P6", "P7", "P7_1", "P7_2", "P7_3", "P7_4", "P7_5", "P7_6", "P7_7", "P7_8", 
    "P8", "P9", "P9_2", "P9_3", "P9_4", "P9_1", "P9_5", "P9_6", "P9_7", "P9_8", "P9_9", 
    "P9_10", "P10", "P10_2", "P10_3", "P10_4", "P10_1", "P10_5", "P10_6", "P10_7", "P10_8", 
    "P10_9", "P10_10", "P11", "P12", "P13", "P14", "P15", "P16", "P17", "P18", "P19", 
    "P20", "P21", "P22", "P23", "P24", "P25", "P26", "P27", "P28", "P29", "P30", 
    "P31", "P32", "P33", "P34_1", "P34_2", "P34_3", "P34_4", "P34_5", "P34_6", 
    "P34_7", "P35_2", "P35_3", "P35_4", "P35_1", "P35_5", "P35_6", "P36", "P37_2", 
    "P37_3", "P37_1", "P37_4", "P37_5", "P37_6", "P38_1", "P38_2", "P38_3", "P38_4", 
    "P38_5", "P38_6", "P38_7", "P39", "P40", "P41_1", "P41_2", "P41_3", "P41_4", 
    "P41_5", "P41_6", "P41_7", "P41_8", "P41_9", "P41_10", "P41_11", "P42", "IDADE", 
    "P44", "P45", "P46", "P47", "P48", "ID", "EMP", "FONE", "P52", "audios_urls"
]


def natural_sort_key(column_name: str) -> tuple:
    """
    Cria uma chave de ordenação natural que separa texto e números.
    
    Exemplos:
        'P10_2' -> ('P', 10, '_', 2)
        'P2' -> ('P', 2)
        'Autor' -> ('Autor',)
        'ID Coleta' -> ('ID Coleta',)
    
    Args:
        column_name: Nome da coluna
        
    Returns:
        Tuple com partes alternadas de texto e números para ordenação natural
    """
    # Padrão que captura texto e números alternadamente
    parts = re.split(r'(\d+)', column_name.strip())
    
    # Converter números para int, manter texto como string
    result = []
    for part in parts:
        if part.isdigit():
            result.append(int(part))
        elif part:  # Ignorar strings vazias
            result.append(part)
    
    return tuple(result)


def _extract_question_number(column_name: str) -> tuple:
    """
    Extrai o número da pergunta de colunas que seguem padrões como P1, P3_1, P40, etc.
    
    Args:
        column_name: Nome da coluna
        
    Returns:
        Tuple (é_pergunta, número_principal, número_secundário)
    """
    # Padrão para perguntas: P seguido de número, opcionalmente seguido de _ e outro número
    pattern = r'^P(\d+)(?:_(\d+))?$'
    match = re.match(pattern, column_name.strip(), re.IGNORECASE)
    
    if match:
        main_num = int(match.group(1))
        sub_num = int(match.group(2)) if match.group(2) else 0
        return True, main_num, sub_num
    
    return False, 0, 0


def _build_intelligent_column_order(all_columns: set, base_order: List[str] = None) -> List[str]:
    """
    Constrói a ordem das colunas baseada no schema gabarito (TEMPLATE_SCHEMA).
    
    Algoritmo:
    1. Descobrir todas as colunas existentes nos dados
    2. Isolar e ordenar colunas P# naturalmente
    3. Reconstruir schema base preservando ordem do gabarito para colunas não-P#
    4. Inserir colunas P# ordenadas na posição correta
    5. Adicionar colunas inesperadas ordenadas alfabeticamente no final
    
    Args:
        all_columns: Conjunto de todos os nomes de colunas
        base_order: Lista com a ordem das colunas da primeira tabela (não usado nesta versão)
        
    Returns:
        Lista ordenada de colunas seguindo o schema gabarito
    """
    # Colunas de rastreabilidade sempre primeiro
    traceability_cols = ['Nome do Arquivo de Origem', 'Nome da Planilha de Origem', 'Índice da Tabela na Planilha']
    
    # 1. Começar com colunas de rastreabilidade
    final_order = []
    for col in traceability_cols:
        if col in all_columns:
            final_order.append(col)
    
    # 2. Filtrar apenas as colunas P# que existem nos dados e ordená-las naturalmente
    discovered_p_columns = [col for col in all_columns if re.match(r'^P\d+', col)]
    p_columns_sorted = sorted(discovered_p_columns, key=natural_sort_key)
    
    # 3. Reconstruir schema base: preservar ordem do gabarito para colunas não-P#
    base_schema = []
    p_inserted = False
    
    for col in TEMPLATE_SCHEMA:
        # Se não for coluna P# e existir nos dados, adicionar
        if not re.match(r'^P\d+', col) and col in all_columns and col not in traceability_cols:
            base_schema.append(col)
        # Se for a primeira coluna P# encontrada no gabarito, inserir todas as colunas P# ordenadas
        elif re.match(r'^P\d+', col) and not p_inserted and p_columns_sorted:
            base_schema.extend(p_columns_sorted)
            p_inserted = True
    
    # 4. Se não inserimos P# ainda (não havia P# no gabarito), mas temos colunas P#, adicionar no final das conhecidas
    if not p_inserted and p_columns_sorted:
        base_schema.extend(p_columns_sorted)
    
    # 5. Adicionar schema base à ordem final
    final_order.extend(base_schema)
    
    # 6. Encontrar colunas inesperadas (que não estão no gabarito nem são de rastreabilidade)
    all_known_columns = set(traceability_cols) | set(TEMPLATE_SCHEMA)
    unexpected_columns = [col for col in all_columns if col not in all_known_columns]
    
    # 7. Ordenar colunas inesperadas alfabeticamente e adicionar no final
    unexpected_columns.sort()
    final_order.extend(unexpected_columns)
    
    # 8. Remover duplicatas preservando ordem
    seen = set()
    final_order = [col for col in final_order if not (col in seen or seen.add(col))]
    
    return final_order


def consolidate_data(dataframes_generator: Generator[pd.DataFrame, None, None]) -> Tuple[pd.DataFrame, str]:
    """
    Consolidates multiple DataFrames into a single DataFrame using SQLite with intelligent column ordering.
    
    Args:
        dataframes_generator: Generator yielding pandas DataFrames to consolidate
        
    Returns:
        Tuple containing:
        - Consolidated DataFrame with all data
        - Anomaly report string
    """
    # Phase 1: Discovery - Build master column list
    print("Phase 1: Discovering all unique columns...")
    all_columns = set()
    dataframes_list = []
    base_order = None  # Ordem da primeira tabela
    
    for idx, df in enumerate(dataframes_generator):
        if df.empty:
            continue
            
        # Clean column names (strip whitespace, handle NaN)
        df.columns = [str(col).strip() for col in df.columns]
        dataframes_list.append((idx, df))
        all_columns.update(df.columns)
        
        # Capturar ordem da primeira tabela como base_order
        if base_order is None:
            base_order = list(df.columns)
    
    if not all_columns:
        return pd.DataFrame(), "No data found in any tables"
    
    # Phase 1.5: Build intelligent column order
    print("Phase 1.5: Building intelligent column order...")
    master_columns = _build_intelligent_column_order(all_columns, base_order)
    print(f"Found {len(master_columns)} unique columns in intelligent order")
    
    # Phase 2: Structure - Create SQLite table
    print("Phase 2: Creating SQLite database structure...")
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    conn = sqlite3.connect(temp_db.name)
    
    try:
        # Create table with all columns as TEXT to handle mixed data types
        columns_sql = ', '.join([f'`{col}` TEXT' for col in master_columns])
        create_table_sql = f"CREATE TABLE consolidada ({columns_sql})"
        conn.execute(create_table_sql)
        conn.commit()
        
        # Phase 3: Load - Insert data from each DataFrame
        print("Phase 3: Loading data into database...")
        anomaly_reports = []
        
        for table_idx, df in dataframes_list:
            if df.empty:
                continue
            
            # Get traceability info from DataFrame if available
            file_name = df['Nome do Arquivo de Origem'].iloc[0] if 'Nome do Arquivo de Origem' in df.columns else 'Unknown'
            sheet_name = df['Nome da Planilha de Origem'].iloc[0] if 'Nome da Planilha de Origem' in df.columns else 'Unknown'
            table_idx_in_sheet = df['Índice da Tabela na Planilha'].iloc[0] if 'Índice da Tabela na Planilha' in df.columns else table_idx + 1
                
            # Check for missing columns
            missing_cols = set(master_columns) - set(df.columns)
            if missing_cols:
                missing_cols_list = sorted([col for col in missing_cols if col not in ['Nome do Arquivo de Origem', 'Nome da Planilha de Origem', 'Índice da Tabela na Planilha']])
                if missing_cols_list:
                    anomaly_reports.append(
                        f"{file_name} -> {sheet_name} -> Tabela {table_idx_in_sheet}: {missing_cols_list}"
                    )
            
            # Create a DataFrame with all master columns, filling missing ones with None
            aligned_df = pd.DataFrame(columns=master_columns)
            for col in df.columns:
                if col in master_columns:
                    aligned_df[col] = df[col].astype(str).replace('nan', None)
            
            # Insert into SQLite
            aligned_df.to_sql('consolidada', conn, if_exists='append', index=False)
        
        # Phase 4: Final - Generate result and cleanup
        print("Phase 4: Generating final result...")
        
        # Query with explicit column order
        columns_query = ', '.join([f'`{col}`' for col in master_columns])
        result_df = pd.read_sql_query(f"SELECT {columns_query} FROM consolidada", conn)
        
        # Format anomaly report
        report_text = "\n".join(anomaly_reports) if anomaly_reports else "Nenhuma anomalia detectada."
        
        return result_df, report_text
        
    finally:
        conn.close()
        # Clean up temporary database file
        try:
            os.unlink(temp_db.name)
        except OSError:
            pass