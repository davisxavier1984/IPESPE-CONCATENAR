import pytest
import pandas as pd
import io
from file_handler import parse_excel_files, create_downloadable_excel


def create_test_excel_file(data_dict):
    """
    Helper function to create test Excel files in memory.
    
    Args:
        data_dict: Dictionary where keys are sheet names and values are lists of DataFrames
    
    Returns:
        io.BytesIO: Excel file in memory
    """
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        for sheet_name, dataframes in data_dict.items():
            # Start writing from row 0
            current_row = 0
            
            for i, df in enumerate(dataframes):
                # Write DataFrame
                df.to_excel(writer, sheet_name=sheet_name, startrow=current_row, 
                           index=False, header=True)
                current_row += len(df) + 1  # +1 for header
                
                # Add empty row between tables (except for the last one)
                if i < len(dataframes) - 1:
                    current_row += 1
    
    buffer.seek(0)
    return buffer


class MockUploadedFile:
    """Mock class to simulate Streamlit uploaded file"""
    def __init__(self, buffer, name):
        self.buffer = buffer
        self.name = name
        self.position = 0
    
    def seek(self, position, whence=0):
        self.position = position
        return self.buffer.seek(position, whence)
    
    def read(self, size=-1):
        return self.buffer.read(size)
    
    def getvalue(self):
        return self.buffer.getvalue()
    
    def tell(self):
        return self.buffer.tell()
    
    def seekable(self):
        return True
    
    def readable(self):
        return True
    
    def close(self):
        return self.buffer.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass


def test_parse_excel_files_single_table_single_sheet():
    """Test parsing a single table in a single sheet"""
    # Create test data
    test_df = pd.DataFrame({
        'Name': ['Alice', 'Bob', 'Charlie'],
        'Age': [25, 30, 35],
        'City': ['NYC', 'LA', 'Chicago']
    })
    
    # Create Excel file
    excel_buffer = create_test_excel_file({'Sheet1': [test_df]})
    mock_file = MockUploadedFile(excel_buffer, 'test_single.xlsx')
    
    # Parse file
    tables = list(parse_excel_files([mock_file]))
    
    # Assertions - now includes traceability columns
    assert len(tables) == 1
    assert tables[0].shape == (3, 6)  # 3 original + 3 traceability columns
    
    # Check traceability columns are present
    expected_cols = ['Nome do Arquivo de Origem', 'Nome da Planilha de Origem', 'Índice da Tabela na Planilha', 'Name', 'Age', 'City']
    assert list(tables[0].columns) == expected_cols
    
    # Check traceability data
    assert tables[0]['Nome do Arquivo de Origem'].iloc[0] == 'test_single.xlsx'
    assert tables[0]['Nome da Planilha de Origem'].iloc[0] == 'Sheet1'
    assert tables[0]['Índice da Tabela na Planilha'].iloc[0] == 1
    
    # Check original data
    assert tables[0]['Name'].tolist() == ['Alice', 'Bob', 'Charlie']


def test_parse_excel_files_multiple_tables_single_sheet():
    """Test parsing multiple tables separated by empty rows in a single sheet"""
    # Create test data
    test_df1 = pd.DataFrame({
        'Product': ['A', 'B'],
        'Price': [10, 20]
    })
    
    test_df2 = pd.DataFrame({
        'Employee': ['John', 'Jane'],
        'Department': ['IT', 'HR']
    })
    
    # Create Excel file
    excel_buffer = create_test_excel_file({'Sheet1': [test_df1, test_df2]})
    mock_file = MockUploadedFile(excel_buffer, 'test_multiple.xlsx')
    
    # Parse file
    tables = list(parse_excel_files([mock_file]))
    
    # Assertions - now includes traceability columns
    assert len(tables) == 2
    assert tables[0].shape == (2, 5)  # 2 original + 3 traceability columns
    assert tables[1].shape == (2, 5)  # 2 original + 3 traceability columns
    
    # Check table indices are different
    assert tables[0]['Índice da Tabela na Planilha'].iloc[0] == 1
    assert tables[1]['Índice da Tabela na Planilha'].iloc[0] == 2
    
    # Check column names (traceability columns come first)
    assert 'Product' in tables[0].columns
    assert 'Price' in tables[0].columns
    assert 'Employee' in tables[1].columns
    assert 'Department' in tables[1].columns


def test_parse_excel_files_multiple_sheets():
    """Test parsing multiple sheets with multiple tables each"""
    # Create test data
    sheet1_df1 = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
    sheet1_df2 = pd.DataFrame({'C': [5, 6], 'D': [7, 8]})
    
    sheet2_df1 = pd.DataFrame({'E': [9, 10], 'F': [11, 12]})
    
    # Create Excel file
    excel_buffer = create_test_excel_file({
        'Sheet1': [sheet1_df1, sheet1_df2],
        'Sheet2': [sheet2_df1]
    })
    mock_file = MockUploadedFile(excel_buffer, 'test_multi_sheet.xlsx')
    
    # Parse file
    tables = list(parse_excel_files([mock_file]))
    
    # Assertions - now includes traceability columns
    assert len(tables) == 3
    assert all(table.shape == (2, 5) for table in tables)  # 2 original + 3 traceability columns
    
    # Check sheet names in traceability
    assert tables[0]['Nome da Planilha de Origem'].iloc[0] == 'Sheet1'
    assert tables[1]['Nome da Planilha de Origem'].iloc[0] == 'Sheet1'
    assert tables[2]['Nome da Planilha de Origem'].iloc[0] == 'Sheet2'
    
    # Check table indices restart for new sheet
    assert tables[0]['Índice da Tabela na Planilha'].iloc[0] == 1  # Sheet1, Table 1
    assert tables[1]['Índice da Tabela na Planilha'].iloc[0] == 2  # Sheet1, Table 2
    assert tables[2]['Índice da Tabela na Planilha'].iloc[0] == 1  # Sheet2, Table 1 (restart)


def test_parse_excel_files_empty_sheet():
    """Test handling of empty sheets"""
    # Create test data with one normal sheet and one empty sheet
    test_df = pd.DataFrame({'X': [1, 2], 'Y': [3, 4]})
    
    # Create Excel file with empty sheet
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        test_df.to_excel(writer, sheet_name='Sheet1', index=False)
        # Create empty sheet
        pd.DataFrame().to_excel(writer, sheet_name='EmptySheet', index=False)
    
    buffer.seek(0)
    mock_file = MockUploadedFile(buffer, 'test_empty_sheet.xlsx')
    
    # Parse file
    tables = list(parse_excel_files([mock_file]))
    
    # Assertions - should only get table from non-empty sheet, now with traceability columns
    assert len(tables) == 1
    assert tables[0].shape == (2, 5)  # 2 original + 3 traceability columns


def test_parse_excel_files_multiple_files():
    """Test parsing multiple files"""
    # Create two test files
    df1 = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
    df2 = pd.DataFrame({'C': [5, 6], 'D': [7, 8]})
    
    file1 = create_test_excel_file({'Sheet1': [df1]})
    file2 = create_test_excel_file({'Sheet1': [df2]})
    
    mock_file1 = MockUploadedFile(file1, 'file1.xlsx')
    mock_file2 = MockUploadedFile(file2, 'file2.xlsx')
    
    # Parse files
    tables = list(parse_excel_files([mock_file1, mock_file2]))
    
    # Assertions - check file names in traceability
    assert len(tables) == 2
    assert tables[0]['Nome do Arquivo de Origem'].iloc[0] == 'file1.xlsx'
    assert tables[1]['Nome do Arquivo de Origem'].iloc[0] == 'file2.xlsx'
    
    # Check that original columns are still present
    assert 'A' in tables[0].columns
    assert 'B' in tables[0].columns
    assert 'C' in tables[1].columns
    assert 'D' in tables[1].columns


def test_create_downloadable_excel_basic():
    """Test basic functionality of create_downloadable_excel"""
    # Create test DataFrame
    test_df = pd.DataFrame({
        'Name': ['Alice', 'Bob', 'Charlie'],
        'Age': [25, 30, 35],
        'Salary': [50000, 60000, 70000]
    })
    
    # Create downloadable Excel
    excel_bytes = create_downloadable_excel(test_df)
    
    # Assertions
    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 0


def test_create_downloadable_excel_content_validation():
    """Test that the downloadable Excel contains correct data"""
    # Create test DataFrame
    test_df = pd.DataFrame({
        'Product': ['A', 'B', 'C'],
        'Quantity': [10, 20, 30],
        'Price': [100.5, 200.0, 300.75]
    })
    
    # Create downloadable Excel
    excel_bytes = create_downloadable_excel(test_df)
    
    # Read back the Excel data to validate
    read_back_df = pd.read_excel(io.BytesIO(excel_bytes), sheet_name='Consolidated_Data')
    
    # Assertions
    assert read_back_df.shape == test_df.shape
    assert list(read_back_df.columns) == list(test_df.columns)
    assert read_back_df['Product'].tolist() == test_df['Product'].tolist()
    assert read_back_df['Quantity'].tolist() == test_df['Quantity'].tolist()
    assert read_back_df['Price'].tolist() == test_df['Price'].tolist()


def test_create_downloadable_excel_empty_dataframe():
    """Test handling of empty DataFrame"""
    empty_df = pd.DataFrame()
    
    # Should not raise exception
    excel_bytes = create_downloadable_excel(empty_df)
    
    # Assertions
    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 0
    
    # Read back to ensure it's valid Excel
    read_back_df = pd.read_excel(io.BytesIO(excel_bytes), sheet_name='Consolidated_Data')
    assert read_back_df.empty


if __name__ == '__main__':
    pytest.main([__file__])