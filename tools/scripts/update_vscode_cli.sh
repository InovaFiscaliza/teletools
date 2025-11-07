#!/bin/bash

# Script para atualizar o VSCode CLI no Linux
# Requer permissões de superusuário (root)

set -e  # Encerra o script se houver erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # Sem cor

# URL de download
URL="https://update.code.visualstudio.com/latest/cli-linux-x64/stable"
INSTALL_DIR="/usr/local/bin"
TEMP_DIR=$(mktemp -d)

echo -e "${YELLOW}Iniciando atualização do VSCode CLI...${NC}"

# Verifica se está rodando como root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Este script precisa ser executado como root (sudo)${NC}"
    exit 1
fi

# Função de limpeza em caso de erro
cleanup() {
    echo -e "${YELLOW}Limpando arquivos temporários...${NC}"
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# Baixa a versão mais recente
echo -e "${YELLOW}Baixando VSCode CLI...${NC}"
if ! curl -L "$URL" -o "$TEMP_DIR/vscode_cli.tar.gz" --progress-bar; then
    echo -e "${RED}Erro ao baixar o VSCode CLI${NC}"
    exit 1
fi

# Extrai o arquivo
echo -e "${YELLOW}Extraindo arquivo...${NC}"
if ! tar -xzf "$TEMP_DIR/vscode_cli.tar.gz" -C "$TEMP_DIR"; then
    echo -e "${RED}Erro ao extrair o arquivo${NC}"
    exit 1
fi

# Encontra o executável 'code' no diretório extraído
CODE_BIN=$(find "$TEMP_DIR" -name "code" -type f | head -n 1)

if [ -z "$CODE_BIN" ]; then
    echo -e "${RED}Executável 'code' não encontrado no arquivo baixado${NC}"
    exit 1
fi

# Faz backup da versão anterior se existir
if [ -f "$INSTALL_DIR/code" ]; then
    echo -e "${YELLOW}Fazendo backup da versão anterior...${NC}"
    mv "$INSTALL_DIR/code" "$INSTALL_DIR/code.backup"
fi

# Move o executável para o diretório de instalação
echo -e "${YELLOW}Instalando VSCode CLI em $INSTALL_DIR...${NC}"
mv "$CODE_BIN" "$INSTALL_DIR/code"
chmod +x "$INSTALL_DIR/code"

# Verifica a instalação
if [ -f "$INSTALL_DIR/code" ] && [ -x "$INSTALL_DIR/code" ]; then
    echo -e "${GREEN}✓ VSCode CLI atualizado com sucesso!${NC}"
    echo -e "${GREEN}Versão instalada:${NC}"
    "$INSTALL_DIR/code" --version
    
    # Remove o backup se a instalação foi bem-sucedida
    if [ -f "$INSTALL_DIR/code.backup" ]; then
        rm "$INSTALL_DIR/code.backup"
    fi
else
    echo -e "${RED}Erro na instalação${NC}"
    # Restaura o backup se houver
    if [ -f "$INSTALL_DIR/code.backup" ]; then
        echo -e "${YELLOW}Restaurando versão anterior...${NC}"
        mv "$INSTALL_DIR/code.backup" "$INSTALL_DIR/code"
    fi
    exit 1
fi

echo -e "${GREEN}Atualização concluída!${NC}"