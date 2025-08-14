# Como Gerar o Executável para Windows

## Requisitos
- Python 3.8 ou superior instalado
- Windows 10 ou superior

## Passos para Gerar o Executável

### Método 1: Script Automático (Recomendado)
1. Abra o Prompt de Comando como Administrador
2. Navegue até a pasta do projeto
3. Execute o script: `build_exe.bat`
4. Aguarde a conclusão do processo
5. O executável estará em `dist\ConsolidadorExcel.exe`

### Método 2: Manual
```bash
# 1. Criar ambiente virtual
python -m venv venv

# 2. Ativar ambiente virtual
venv\Scripts\activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Gerar executável
pyinstaller app.spec
```

## Como Usar o Executável
1. Navegue até a pasta `dist`
2. Execute `ConsolidadorExcel.exe`
3. O aplicativo abrirá automaticamente no seu navegador
4. Faça upload dos arquivos Excel e clique em "Consolidar"

## Solução de Problemas

### Erro: "Python não encontrado"
- Verifique se o Python está instalado e no PATH do sistema

### Erro: "PyInstaller não encontrado" 
- Execute: `pip install pyinstaller`

### Executável não abre
- Execute pelo Prompt de Comando para ver mensagens de erro
- Verifique se todas as dependências foram incluídas

### Antivírus bloqueia o executável
- Adicione exceção para a pasta `dist`
- Alguns antivírus detectam falsos positivos em executáveis PyInstaller

## Arquivos Gerados
- `ConsolidadorExcel.exe` - Executável principal
- `dist\` - Pasta com o executável final
- `build\` - Pasta temporária (pode ser deletada após build)

## Distribuição
O arquivo `ConsolidadorExcel.exe` pode ser distribuído independentemente e não requer instalação do Python no computador de destino.