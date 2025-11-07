#!/bin/bash

# Script simples para criação de usuário no RHEL
# Senha padrão: Anatel123
# Grupos: cdr, docker
# Shell: bash

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Funções de mensagem
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Verificar se está rodando como root
if [[ $EUID -ne 0 ]]; then
    print_error "Este script precisa ser executado como root (sudo)"
    exit 1
fi

# Verificar se o username foi passado como parâmetro
if [[ -z "$1" ]]; then
    print_error "Uso: $0 <username>"
    echo "Exemplo: $0 rafael"
    exit 1
fi

username="$1"


# Verificar se o usuário já existe
if id "$username" &>/dev/null; then
    print_error "O usuário '$username' já existe!"
    exit 1
fi

# Exibir resumo
echo
# Banner
echo -e "╔═══════════════════════════════════════════════╗"
echo -e "║          Criação de Usuário - Resumo          ║"
echo -e "║                                               ║"
printf "║  Username: ${BLUE}%-35s${NC}║\n" "$username"
echo -e "║  Senha inicial: ${BLUE}Anatel123${NC}                     ║"
echo -e "║  Grupos: ${BLUE}cdr, docker${NC}                          ║"
echo -e "║  Shell: ${BLUE}/bin/bash${NC}                             ║"
echo -e "║                                               ║"
echo -e "╚═══════════════════════════════════════════════╝"

read -p "Confirma a criação? (S/n): " confirm
confirm=${confirm:-S}

if [[ "$confirm" != "s" && "$confirm" != "S" ]]; then
    print_error "Operação cancelada"
    exit 0
fi

# Criar o usuário
print_info "Criando usuário..."

if useradd -m -s /bin/bash -G cdr,docker "$username"; then
    print_success "Usuário criado"
else
    print_error "Erro ao criar usuário"
    exit 1
fi

# Definir senha
if echo "$username:Anatel123" | chpasswd; then
    print_success "Senha definida"
else
    print_error "Erro ao definir senha"
    exit 1
fi

# Forçar mudança de senha no primeiro login
if passwd -e "$username" &>/dev/null; then
    print_success "Senha expirada (mudança obrigatória no primeiro login)"
fi

# Exibir resultado
echo
print_success "Usuário '$username' criado com sucesso!"
echo
print_info "Informações:"
id "$username"
echo

# Criar outro usuário
read -p "Deseja criar outro usuário? (s/N): " another
if [[ "$another" == "s" || "$another" == "S" ]]; then
    echo
    read -p "Digite o nome do usuário: " new_username
    exec "$0" "$new_username"
fi

print_info "Concluído!"