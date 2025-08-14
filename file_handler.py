import pandas as pd
import io


def parse_excel_files(uploaded_files):
    """
    Lê uma lista de arquivos Excel carregados e extrai todas as tabelas individuais
    de todas as planilhas, adicionando colunas de rastreabilidade.

    Args:
        uploaded_files: Uma lista de objetos de arquivo carregados pelo Streamlit.

    Returns:
        tuple: (generator, source_manifest)
            - generator: Um gerador que produz DataFrames para cada tabela encontrada
            - source_manifest: Lista de dicionários com informações de rastreabilidade
    """
    source_manifest = []
    table_data_list = []
    
    for uploaded_file in uploaded_files:
        # Reset file pointer to beginning
        uploaded_file.seek(0)
        
        try:
            # Load Excel file
            excel_file = pd.ExcelFile(uploaded_file)
            
            # Iterate through each sheet
            for sheet_name in excel_file.sheet_names:
                # Read the entire sheet
                df_sheet = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
                
                # Skip empty sheets
                if df_sheet.empty:
                    continue
                
                # Find completely empty rows
                empty_rows = df_sheet.isnull().all(axis=1)
                empty_row_indices = df_sheet[empty_rows].index.tolist()
                
                # Add boundaries at start and end
                boundaries = [0] + [idx for idx in empty_row_indices] + [len(df_sheet)]
                
                # Counter for table index within this sheet
                table_index = 1
                
                # Extract tables between boundaries
                for i in range(len(boundaries) - 1):
                    start_idx = boundaries[i]
                    end_idx = boundaries[i + 1]
                    
                    # Skip if this is an empty row boundary
                    if start_idx in empty_row_indices:
                        start_idx += 1
                    
                    # Extract table data
                    if start_idx < end_idx:
                        table_data = df_sheet.iloc[start_idx:end_idx].copy()
                        
                        # Remove completely empty rows and columns
                        table_data = table_data.dropna(how='all', axis=0)
                        table_data = table_data.dropna(how='all', axis=1)
                        
                        # Skip if table is empty after cleaning
                        if table_data.empty:
                            continue
                        
                        # Reset index
                        table_data = table_data.reset_index(drop=True)
                        
                        # Count rows before header processing (this will be our data row count)
                        data_row_count = len(table_data)
                        
                        # Set first row as header if it contains non-null values
                        if not table_data.empty and not table_data.iloc[0].isnull().all():
                            # Use first row as column names
                            table_data.columns = table_data.iloc[0].astype(str)
                            table_data = table_data.drop(table_data.index[0]).reset_index(drop=True)
                            
                            # Clean column names (remove NaN)
                            table_data.columns = [col if col != 'nan' else f'Column_{i}' 
                                                for i, col in enumerate(table_data.columns)]
                            
                            # Update data row count after removing header
                            data_row_count = len(table_data)
                        
                        # Add traceability columns if table has data
                        if not table_data.empty:
                            # Insert traceability columns at the beginning
                            table_data.insert(0, 'Nome do Arquivo de Origem', uploaded_file.name)
                            table_data.insert(1, 'Nome da Planilha de Origem', sheet_name)
                            table_data.insert(2, 'Índice da Tabela na Planilha', table_index)
                            
                            # Add to manifest
                            source_manifest.append({
                                'file_name': uploaded_file.name,
                                'sheet_name': sheet_name,
                                'table_index': table_index,
                                'row_count': data_row_count
                            })
                            
                            # Store table data for generator
                            table_data_list.append(table_data)
                            table_index += 1
                            
        except Exception as e:
            # Skip problematic files but continue processing others
            print(f"Error processing file {uploaded_file.name}: {str(e)}")
            continue
    
    # Create generator from stored table data
    def table_generator():
        for table_data in table_data_list:
            yield table_data
    
    return table_generator(), source_manifest


def create_downloadable_excel(df):
    """
    Converte um DataFrame em um objeto de bytes de um arquivo Excel para download.

    Args:
        df (pd.DataFrame): O DataFrame consolidado final.

    Returns:
        bytes: Os dados do arquivo Excel prontos para serem baixados.
    """
    # Create in-memory buffer
    output_buffer = io.BytesIO()
    
    # Write DataFrame to Excel in memory
    with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Consolidated_Data')
    
    # Rewind buffer to beginning
    output_buffer.seek(0)
    
    # Return bytes data
    return output_buffer.getvalue()