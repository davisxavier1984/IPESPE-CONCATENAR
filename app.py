import streamlit as st
import pandas as pd
import file_handler
import database_processor

# --- Configuração da Página e Títulos ---
st.set_page_config(page_title="Consolidador Excel", layout="wide")
st.title("📊 Consolidador de Planilhas Excel")
st.markdown(
    "Faça o upload de múltiplos arquivos Excel para consolidar tabelas empilhadas "
    "de forma inteligente."
)

# --- Componente de Upload ---
uploaded_files = st.file_uploader(
    "Selecione um ou mais arquivos Excel",
    type=['xlsx', 'xls'],
    accept_multiple_files=True
)

# --- Lógica de Processamento (só executa se houver arquivos) ---
if uploaded_files:
    st.info(f"{len(uploaded_files)} arquivo(s) selecionado(s). Clique abaixo para iniciar.")

    if st.button("🚀 Consolidar Arquivos"):
        try:
            # Envolve o processo em um spinner para feedback visual
            with st.spinner("Processando... Isso pode levar alguns minutos dependendo do tamanho dos arquivos."):
                
                # 1. Chama o file_handler para começar a ler os arquivos
                dataframes_generator = file_handler.parse_excel_files(uploaded_files)

                # 2. Chama o database_processor para fazer a consolidação
                final_df, report_log = database_processor.consolidate_data(dataframes_generator)
            
            # --- Exibição dos Resultados ---
            st.success("🎉 Consolidação concluída com sucesso!")

            # Armazena os resultados no estado da sessão para que não se percam
            st.session_state['final_df'] = final_df
            st.session_state['report_log'] = report_log
            st.session_state['processed'] = True

        except Exception as e:
            st.error(f"Ocorreu um erro durante o processamento: {e}")
            st.exception(e) # Exibe o traceback completo para depuração
            st.session_state['processed'] = False


# --- Exibição Permanente dos Resultados após o processamento ---
if st.session_state.get('processed', False):
    
    st.subheader("📋 Relatório de Anomalias")
    st.text_area(
        "Colunas ausentes encontradas (Arquivo -> Planilha -> Tabela):", 
        value=st.session_state['report_log'], 
        height=200
    )

    st.subheader("📄 Pré-visualização dos Dados Consolidados")
    st.dataframe(st.session_state['final_df'])

    # 3. Prepara o arquivo para download usando o file_handler
    excel_data = file_handler.create_downloadable_excel(st.session_state['final_df'])
    
    st.download_button(
        label="📥 Baixar Arquivo Consolidado (.xlsx)",
        data=excel_data,
        file_name="dados_consolidados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )