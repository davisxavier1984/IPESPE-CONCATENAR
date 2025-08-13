import pandas as pd
from database_processor import consolidate_data, TEMPLATE_SCHEMA
import re


def test_consolidate_data_basic():
    """Test basic consolidation with matching columns"""
    
    # Create test DataFrames with traceability columns (simulating file_handler output)
    df1 = pd.DataFrame({
        'Nome do Arquivo de Origem': ['test1.xlsx', 'test1.xlsx'],
        'Nome da Planilha de Origem': ['Sheet1', 'Sheet1'],
        'Índice da Tabela na Planilha': [1, 1],
        'Nome': ['Alice', 'Bob'],
        'Idade': [25, 30],
        'Cidade': ['SP', 'RJ']
    })
    
    df2 = pd.DataFrame({
        'Nome do Arquivo de Origem': ['test2.xlsx', 'test2.xlsx'],
        'Nome da Planilha de Origem': ['Sheet1', 'Sheet1'],
        'Índice da Tabela na Planilha': [1, 1],
        'Nome': ['Carol', 'David'],
        'Idade': [28, 35],
        'Cidade': ['BH', 'PE']
    })
    
    # Convert to generator
    def data_generator():
        yield df1
        yield df2
    
    # Test consolidation
    result_df, anomalies = consolidate_data(data_generator())
    
    # Debug output
    print(f"Basic test - Column order: {list(result_df.columns)}")
    
    # Assertions - expect traceability columns first, then ordered according to template schema logic
    assert len(result_df) == 4
    # Com a nova lógica, colunas não-P# são ordenadas alfabeticamente já que não estão no gabarito
    expected_cols = ['Nome do Arquivo de Origem', 'Nome da Planilha de Origem', 'Índice da Tabela na Planilha', 'Cidade', 'Idade', 'Nome']
    assert list(result_df.columns) == expected_cols
    assert "Nenhuma anomalia detectada" in anomalies
    assert 'Alice' in result_df['Nome'].values
    assert 'Carol' in result_df['Nome'].values


def test_consolidate_data_missing_columns():
    """Test consolidation with missing columns (anomalies)"""
    
    df1 = pd.DataFrame({
        'Nome do Arquivo de Origem': ['test1.xlsx', 'test1.xlsx'],
        'Nome da Planilha de Origem': ['Sheet1', 'Sheet1'],
        'Índice da Tabela na Planilha': [1, 1],
        'Nome': ['Alice', 'Bob'],
        'Idade': [25, 30],
        'Email': ['alice@test.com', 'bob@test.com']
    })
    
    df2 = pd.DataFrame({
        'Nome do Arquivo de Origem': ['test2.xlsx'],
        'Nome da Planilha de Origem': ['Sheet1'],
        'Índice da Tabela na Planilha': [1],
        'Nome': ['Carol'],
        'Cidade': ['SP']  # Missing 'Idade' and 'Email'
    })
    
    def data_generator():
        yield df1
        yield df2
    
    result_df, anomalies = consolidate_data(data_generator())
    
    # Debug output
    print(f"Anomalies: {anomalies}")
    print(f"Result columns: {list(result_df.columns)}")
    print(f"Result shape: {result_df.shape}")
    
    # Should have all columns including traceability
    assert len(result_df) == 3
    expected_cols = {'Nome do Arquivo de Origem', 'Nome da Planilha de Origem', 'Índice da Tabela na Planilha', 'Cidade', 'Email', 'Idade', 'Nome'}
    assert set(result_df.columns) == expected_cols
    
    # Check that anomalies are reported with new format
    assert "test1.xlsx -> Sheet1 -> Tabela 1" in anomalies or "test2.xlsx -> Sheet1 -> Tabela 1" in anomalies


def test_consolidate_data_empty_dataframes():
    """Test with empty DataFrames"""
    
    # Create a DataFrame with traceability columns (simulating file_handler output)
    valid_df = pd.DataFrame({
        'Nome do Arquivo de Origem': ['test.xlsx'],
        'Nome da Planilha de Origem': ['Sheet1'],
        'Índice da Tabela na Planilha': [1],
        'Nome': ['Alice'], 
        'Idade': [25]
    })
    
    def data_generator():
        yield pd.DataFrame()  # Empty DataFrame
        yield valid_df
        yield pd.DataFrame()  # Another empty DataFrame
    
    result_df, anomalies = consolidate_data(data_generator())
    
    assert len(result_df) == 1
    assert result_df['Nome'].iloc[0] == 'Alice'
    assert "Nenhuma anomalia detectada" in anomalies


def test_consolidate_data_no_data():
    """Test with no valid data"""
    
    def data_generator():
        yield pd.DataFrame()
        yield pd.DataFrame()
    
    result_df, anomalies = consolidate_data(data_generator())
    
    assert result_df.empty
    assert "No data found" in anomalies


def test_consolidate_data_column_name_cleaning():
    """Test column name cleaning (whitespace handling)"""
    
    df1 = pd.DataFrame({
        'Nome do Arquivo de Origem': ['test1.xlsx'],
        'Nome da Planilha de Origem': ['Sheet1'],
        'Índice da Tabela na Planilha': [1],
        ' Nome ': ['Alice'],  # Column with spaces
        'Idade': [25]
    })
    
    df2 = pd.DataFrame({
        'Nome do Arquivo de Origem': ['test2.xlsx'],
        'Nome da Planilha de Origem': ['Sheet1'],
        'Índice da Tabela na Planilha': [1],
        'Nome': ['Bob'],  # Clean column name
        ' Cidade ': ['SP']  # Column with spaces
    })
    
    def data_generator():
        yield df1
        yield df2
    
    result_df, anomalies = consolidate_data(data_generator())
    
    # Should clean column names and consolidate properly
    assert 'Nome' in result_df.columns
    assert 'Cidade' in result_df.columns
    assert len(result_df) == 2


def test_consolidate_data_mixed_data_types():
    """Test handling of mixed data types"""
    
    df1 = pd.DataFrame({
        'Nome do Arquivo de Origem': ['test1.xlsx', 'test1.xlsx'],
        'Nome da Planilha de Origem': ['Sheet1', 'Sheet1'],
        'Índice da Tabela na Planilha': [1, 1],
        'ID': [1, 2],
        'Nome': ['Alice', 'Bob'],
        'Ativo': [True, False],
        'Salario': [1500.50, 2000.75]
    })
    
    df2 = pd.DataFrame({
        'Nome do Arquivo de Origem': ['test2.xlsx', 'test2.xlsx'],
        'Nome da Planilha de Origem': ['Sheet1', 'Sheet1'],
        'Índice da Tabela na Planilha': [1, 1],
        'ID': ['3', '4'],  # String instead of int
        'Nome': ['Carol', 'David'],
        'Ativo': ['Sim', 'Não'],  # String instead of bool
        'Categoria': ['A', 'B']  # New column
    })
    
    def data_generator():
        yield df1
        yield df2
    
    result_df, anomalies = consolidate_data(data_generator())
    
    # Should handle all data as strings in SQLite
    assert len(result_df) == 4
    # Check that each table has anomalies for missing columns
    assert "test1.xlsx -> Sheet1 -> Tabela 1" in anomalies
    assert "test2.xlsx -> Sheet1 -> Tabela 1" in anomalies


def test_consolidate_data_intelligent_column_ordering():
    """Test intelligent column ordering with question patterns"""
    
    df1 = pd.DataFrame({
        'Nome do Arquivo de Origem': ['test1.xlsx', 'test1.xlsx'],
        'Nome da Planilha de Origem': ['Sheet1', 'Sheet1'],
        'Índice da Tabela na Planilha': [1, 1],
        'Nome': ['Alice', 'Bob'],
        'P1': ['Resp1', 'Resp2'],
        'Idade': [25, 30],
        'P3': ['Resp3', 'Resp4']
    })
    
    df2 = pd.DataFrame({
        'Nome do Arquivo de Origem': ['test2.xlsx', 'test2.xlsx'],
        'Nome da Planilha de Origem': ['Sheet1', 'Sheet1'],
        'Índice da Tabela na Planilha': [1, 1],
        'Nome': ['Carol', 'David'],
        'P2': ['Resp5', 'Resp6'],
        'P1': ['Resp7', 'Resp8'],
        'Cidade': ['SP', 'RJ']
    })
    
    def data_generator():
        yield df1
        yield df2
    
    result_df, anomalies = consolidate_data(data_generator())
    
    # Debug output
    print(f"Column order: {list(result_df.columns)}")
    
    # Check that traceability columns come first
    columns = list(result_df.columns)
    assert columns[0] == 'Nome do Arquivo de Origem'
    assert columns[1] == 'Nome da Planilha de Origem'
    assert columns[2] == 'Índice da Tabela na Planilha'
    
    # Check that questions are ordered numerically (P1, P2, P3)
    p_columns = [col for col in columns if col.startswith('P')]
    assert p_columns == ['P1', 'P2', 'P3']
    
    assert len(result_df) == 4


def test_consolidate_data_natural_ordering():
    """Test natural ordering specifically for P2, P10, P11 sequence"""
    
    # Primeira tabela com colunas não sequenciais
    df1 = pd.DataFrame({
        'Nome do Arquivo de Origem': ['test1.xlsx'],
        'Nome da Planilha de Origem': ['Sheet1'],
        'Índice da Tabela na Planilha': [1],
        'ID': ['001'],
        'P1': ['Resp1'],
        'P10': ['Resp10']  # P10 antes de P2
    })
    
    # Segunda tabela descobrindo P2 e P11
    df2 = pd.DataFrame({
        'Nome do Arquivo de Origem': ['test2.xlsx'],
        'Nome da Planilha de Origem': ['Sheet1'],
        'Índice da Tabela na Planilha': [1],
        'ID': ['002'],
        'P2': ['Resp2'],   # P2 vem depois
        'P11': ['Resp11']  # P11 vem depois
    })
    
    def data_generator():
        yield df1
        yield df2
    
    result_df, anomalies = consolidate_data(data_generator())
    
    # Debug output
    print(f"Natural ordering test - Column order: {list(result_df.columns)}")
    
    # Verificar ordem natural: P1, P2, P10, P11 (não alfabética P1, P10, P11, P2)
    columns = list(result_df.columns)
    p_columns = [col for col in columns if col.startswith('P')]
    
    # Ordem esperada: P1, P2, P10, P11 (ordem natural, não alfabética)
    expected_p_order = ['P1', 'P2', 'P10', 'P11']
    assert p_columns == expected_p_order, f"Esperado {expected_p_order}, obtido {p_columns}"
    
    # Verificar que ID é uma coluna inesperada e vem no final
    id_index = columns.index('ID')
    p1_index = columns.index('P1')
    assert id_index > p1_index, "ID é uma coluna inesperada e deveria vir no final, após as perguntas P#"
    
    assert len(result_df) == 2


def test_consolidate_data_template_schema_ordering():
    """Test ordenação baseada no TEMPLATE_SCHEMA gabarito"""
    
    # Criar dados com algumas colunas do gabarito em ordem diferente
    df1 = pd.DataFrame({
        'Nome do Arquivo de Origem': ['test1.xlsx'],
        'Nome da Planilha de Origem': ['Sheet1'],
        'Índice da Tabela na Planilha': [1],
        'P10': ['Resp10'],  # P10 aparece primeiro nos dados
        'ID Coleta': ['ID001'],
        'P1': ['Resp1'],
        'Autor': ['João'],
        'P2': ['Resp2']
    })
    
    df2 = pd.DataFrame({
        'Nome do Arquivo de Origem': ['test2.xlsx'],
        'Nome da Planilha de Origem': ['Sheet1'],
        'Índice da Tabela na Planilha': [1],
        'P5': ['Resp5'],
        'Data início': ['2024-01-01'],
        'P3': ['Resp3'],
        'ID Coleta': ['ID002']
    })
    
    def data_generator():
        yield df1
        yield df2
    
    result_df, anomalies = consolidate_data(data_generator())
    
    # Debug output
    print(f"Template schema test - Column order: {list(result_df.columns)}")
    
    columns = list(result_df.columns)
    
    # 1. Verificar que colunas de rastreabilidade vêm primeiro
    assert columns[0] == 'Nome do Arquivo de Origem'
    assert columns[1] == 'Nome da Planilha de Origem'
    assert columns[2] == 'Índice da Tabela na Planilha'
    
    # 2. Verificar que colunas não-P# seguem ordem do gabarito
    non_p_columns = [col for col in columns if not re.match(r'^P\d+', col) and col not in ['Nome do Arquivo de Origem', 'Nome da Planilha de Origem', 'Índice da Tabela na Planilha']]
    
    # Ordem esperada conforme TEMPLATE_SCHEMA: ID Coleta, Autor, Data início
    expected_non_p_order = ['ID Coleta', 'Autor', 'Data início']
    actual_non_p_order = [col for col in expected_non_p_order if col in non_p_columns]
    
    # Verificar que as colunas não-P# seguem a ordem do gabarito
    for i, col in enumerate(actual_non_p_order):
        assert col in non_p_columns, f"Coluna {col} deveria estar presente"
        if i > 0:
            prev_col = actual_non_p_order[i-1]
            prev_index = columns.index(prev_col)
            curr_index = columns.index(col)
            assert prev_index < curr_index, f"Ordem incorreta: {prev_col} deveria vir antes de {col}"
    
    # 3. Verificar que colunas P# estão ordenadas naturalmente
    p_columns = [col for col in columns if re.match(r'^P\d+', col)]
    expected_p_order = ['P1', 'P2', 'P3', 'P5', 'P10']
    assert p_columns == expected_p_order, f"Esperado {expected_p_order}, obtido {p_columns}"
    
    # 4. Verificar que P# vêm depois das colunas não-P# do gabarito
    first_p_index = columns.index('P1')
    for col in ['ID Coleta', 'Autor', 'Data início']:
        if col in columns:
            col_index = columns.index(col)
            assert col_index < first_p_index, f"Coluna {col} deveria vir antes das perguntas P#"
    
    assert len(result_df) == 2


def test_consolidate_data_unexpected_columns():
    """Test tratamento de colunas inesperadas (não no gabarito)"""
    
    df1 = pd.DataFrame({
        'Nome do Arquivo de Origem': ['test1.xlsx'],
        'Nome da Planilha de Origem': ['Sheet1'],
        'Índice da Tabela na Planilha': [1],
        'ID Coleta': ['ID001'],
        'P1': ['Resp1'],
        'Nova_Coluna_Z': ['Valor1'],  # Coluna inesperada
        'Nova_Coluna_A': ['Valor2']   # Coluna inesperada
    })
    
    def data_generator():
        yield df1
    
    result_df, anomalies = consolidate_data(data_generator())
    
    # Debug output
    print(f"Unexpected columns test - Column order: {list(result_df.columns)}")
    
    columns = list(result_df.columns)
    
    # Verificar que colunas inesperadas estão no final e ordenadas alfabeticamente
    unexpected_cols = ['Nova_Coluna_A', 'Nova_Coluna_Z']
    
    # Encontrar posições das colunas inesperadas
    nova_a_index = columns.index('Nova_Coluna_A')
    nova_z_index = columns.index('Nova_Coluna_Z')
    
    # Verificar que estão ordenadas alfabeticamente
    assert nova_a_index < nova_z_index, "Colunas inesperadas deveriam estar em ordem alfabética"
    
    # Verificar que estão no final (depois de todas as colunas conhecidas)
    p1_index = columns.index('P1')
    assert p1_index < nova_a_index, "Colunas inesperadas deveriam vir no final"
    
    assert len(result_df) == 1


if __name__ == "__main__":
    # Run tests manually
    print("Running database_processor tests...")
    
    test_consolidate_data_basic()
    print("✓ Basic consolidation test passed")
    
    test_consolidate_data_missing_columns()
    print("✓ Missing columns test passed")
    
    test_consolidate_data_empty_dataframes()
    print("✓ Empty DataFrames test passed")
    
    test_consolidate_data_no_data()
    print("✓ No data test passed")
    
    test_consolidate_data_column_name_cleaning()
    print("✓ Column name cleaning test passed")
    
    test_consolidate_data_mixed_data_types()
    print("✓ Mixed data types test passed")
    
    test_consolidate_data_intelligent_column_ordering()
    print("✓ Intelligent column ordering test passed")
    
    test_consolidate_data_natural_ordering()
    print("✓ Natural ordering test passed")
    
    test_consolidate_data_template_schema_ordering()
    print("✓ Template schema ordering test passed")
    
    test_consolidate_data_unexpected_columns()
    print("✓ Unexpected columns test passed")
    
    print("\nAll tests passed! 🎉")