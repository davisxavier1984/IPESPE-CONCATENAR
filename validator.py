import pandas as pd
from typing import List, Dict


def validate_consolidation(consolidated_df: pd.DataFrame, source_manifest: List[Dict]) -> str:
    """
    Valida a integridade da consolidação comparando contagens de linhas
    entre os dados de origem e o DataFrame consolidado final.
    
    Args:
        consolidated_df: DataFrame consolidado final
        source_manifest: Lista de dicionários com informações das tabelas de origem
    
    Returns:
        str: Relatório detalhado de validação
    """
    # Calcular totais gerais
    total_source_rows = sum(table['row_count'] for table in source_manifest)
    total_consolidated_rows = len(consolidated_df)
    
    # Verificar se totais coincidem
    totals_match = total_source_rows == total_consolidated_rows
    
    # Inicializar relatório
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("🔍 RELATÓRIO DE VALIDAÇÃO DE INTEGRIDADE")
    report_lines.append("=" * 60)
    
    # Resumo geral será atualizado após validação detalhada
    # Placeholder será substituído depois da validação detalhada
    summary_placeholder_index = len(report_lines)
    
    report_lines.append("")
    report_lines.append(f"📊 CONTAGENS TOTAIS:")
    report_lines.append(f"   • Linhas nas tabelas de origem: {total_source_rows:,}")
    report_lines.append(f"   • Linhas no arquivo consolidado: {total_consolidated_rows:,}")
    report_lines.append(f"   • Diferença: {abs(total_source_rows - total_consolidated_rows):,}")
    report_lines.append("")
    
    # Validação detalhada por tabela
    report_lines.append("📋 VALIDAÇÃO DETALHADA POR TABELA:")
    report_lines.append("-" * 60)
    
    # LOGS DE DEPURAÇÃO
    print("\n🔍 DEBUG - Análise de Tipos de Dados:")
    print(f"📄 Primeiros 5 itens do source_manifest:")
    for i, item in enumerate(source_manifest[:5]):
        print(f"  {i+1}. {item}")
    
    print(f"\n📊 Colunas do consolidated_df: {list(consolidated_df.columns)}")
    print(f"\n🔢 Tipos de dados das colunas de rastreabilidade:")
    tracking_columns = ['Nome do Arquivo de Origem', 'Nome da Planilha de Origem', 'Índice da Tabela na Planilha']
    for col in tracking_columns:
        if col in consolidated_df.columns:
            print(f"  {col}: {consolidated_df[col].dtype}")
            print(f"    Primeiros 5 valores únicos: {consolidated_df[col].unique()[:5].tolist()}")
        else:
            print(f"  ❌ COLUNA AUSENTE: {col}")
    
    # CORREÇÃO DE TIPOS - Garantir consistência antes da comparação
    consolidated_df = consolidated_df.copy()
    if 'Nome do Arquivo de Origem' in consolidated_df.columns:
        consolidated_df['Nome do Arquivo de Origem'] = consolidated_df['Nome do Arquivo de Origem'].astype(str)
    if 'Nome da Planilha de Origem' in consolidated_df.columns:
        consolidated_df['Nome da Planilha de Origem'] = consolidated_df['Nome da Planilha de Origem'].astype(str)
    if 'Índice da Tabela na Planilha' in consolidated_df.columns:
        consolidated_df['Índice da Tabela na Planilha'] = consolidated_df['Índice da Tabela na Planilha'].astype(int)
    
    print(f"\n✅ Tipos corrigidos para:")
    for col in tracking_columns:
        if col in consolidated_df.columns:
            print(f"  {col}: {consolidated_df[col].dtype}")
    print("-" * 60)
    
    validation_errors = []
    
    for table_info in source_manifest:
        file_name = table_info['file_name']
        sheet_name = table_info['sheet_name']
        table_index = table_info['table_index']
        expected_rows = table_info['row_count']
        
        # Filtrar linhas correspondentes no DataFrame consolidado
        mask = (
            (consolidated_df['Nome do Arquivo de Origem'] == file_name) &
            (consolidated_df['Nome da Planilha de Origem'] == sheet_name) &
            (consolidated_df['Índice da Tabela na Planilha'] == table_index)
        )
        actual_rows = mask.sum()
        
        # Verificar se as contagens coincidem
        if expected_rows == actual_rows:
            status = "✅ OK"
        else:
            status = "❌ ERRO"
            validation_errors.append({
                'file': file_name,
                'sheet': sheet_name,
                'table': table_index,
                'expected': expected_rows,
                'actual': actual_rows,
                'difference': abs(expected_rows - actual_rows)
            })
        
        report_lines.append(
            f"{status} {file_name} → {sheet_name} → Tabela {table_index}: "
            f"{actual_rows}/{expected_rows} linhas"
        )
    
    # Seção de erros detalhados (se houver)
    if validation_errors:
        report_lines.append("")
        report_lines.append("🚨 DETALHES DOS ERROS ENCONTRADOS:")
        report_lines.append("-" * 60)
        
        for error in validation_errors:
            report_lines.append(
                f"❌ {error['file']} → {error['sheet']} → Tabela {error['table']}:"
            )
            report_lines.append(
                f"   Esperado: {error['expected']} linhas | "
                f"Encontrado: {error['actual']} linhas | "
                f"Diferença: {error['difference']} linhas"
            )
            report_lines.append("")
    
    # Atualizar resumo geral com base na validação detalhada
    has_validation_errors = len(validation_errors) > 0
    overall_success = totals_match and not has_validation_errors
    
    # Inserir resultado geral após o cabeçalho
    if overall_success:
        summary_line = "✅ RESULTADO: SUCESSO - Integridade validada com sucesso!"
    else:
        summary_line = "❌ RESULTADO: FALHA - Discrepância encontrada na consolidação!"
    
    report_lines.insert(summary_placeholder_index, summary_line)
    
    # Resumo final
    report_lines.append("=" * 60)
    if overall_success:
        report_lines.append("🎉 VALIDAÇÃO CONCLUÍDA: Todos os dados foram preservados!")
        report_lines.append("   A consolidação manteve 100% da integridade dos dados.")
    else:
        report_lines.append("⚠️  ATENÇÃO: Foram encontradas discrepâncias!")
        if not totals_match:
            report_lines.append("   • Totais de linhas não coincidem.")
        if has_validation_errors:
            report_lines.append(f"   • {len(validation_errors)} tabela(s) com contagem incorreta.")
        report_lines.append("   Recomenda-se revisar os dados antes de prosseguir.")
    
    report_lines.append("=" * 60)
    
    return "\n".join(report_lines)


def get_validation_summary(consolidated_df: pd.DataFrame, source_manifest: List[Dict]) -> Dict:
    """
    Retorna um resumo simplificado da validação para uso programático.
    
    Args:
        consolidated_df: DataFrame consolidado final
        source_manifest: Lista de dicionários com informações das tabelas de origem
    
    Returns:
        Dict: Resumo da validação com status e métricas
    """
    total_source_rows = sum(table['row_count'] for table in source_manifest)
    total_consolidated_rows = len(consolidated_df)
    totals_match = total_source_rows == total_consolidated_rows
    
    # Verificar validação detalhada por tabela
    validation_errors = 0
    consolidated_df_copy = consolidated_df.copy()
    
    # Garantir consistência de tipos
    if 'Nome do Arquivo de Origem' in consolidated_df_copy.columns:
        consolidated_df_copy['Nome do Arquivo de Origem'] = consolidated_df_copy['Nome do Arquivo de Origem'].astype(str)
    if 'Nome da Planilha de Origem' in consolidated_df_copy.columns:
        consolidated_df_copy['Nome da Planilha de Origem'] = consolidated_df_copy['Nome da Planilha de Origem'].astype(str)
    if 'Índice da Tabela na Planilha' in consolidated_df_copy.columns:
        consolidated_df_copy['Índice da Tabela na Planilha'] = consolidated_df_copy['Índice da Tabela na Planilha'].astype(int)
    
    for table_info in source_manifest:
        file_name = table_info['file_name']
        sheet_name = table_info['sheet_name']
        table_index = table_info['table_index']
        expected_rows = table_info['row_count']
        
        mask = (
            (consolidated_df_copy['Nome do Arquivo de Origem'] == file_name) &
            (consolidated_df_copy['Nome da Planilha de Origem'] == sheet_name) &
            (consolidated_df_copy['Índice da Tabela na Planilha'] == table_index)
        )
        actual_rows = mask.sum()
        
        if expected_rows != actual_rows:
            validation_errors += 1
    
    return {
        'is_valid': totals_match and validation_errors == 0,
        'total_source_rows': total_source_rows,
        'total_consolidated_rows': total_consolidated_rows,
        'difference': abs(total_source_rows - total_consolidated_rows),
        'total_tables': len(source_manifest),
        'validation_errors': validation_errors,
        'totals_match': totals_match
    }