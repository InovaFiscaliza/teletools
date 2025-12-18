> **[← Voltar para Teletools](../README.md)**

# Teletools Cipher API

Índice de referência das APIs públicas do módulo `teletools.cipher`.

---

## Visão Geral

O módulo `teletools.cipher` fornece funcionalidades para criptografia e descriptografia de arquivos e pastas usando GPG (GNU Privacy Guard) com criptografia de chave pública/privada. As APIs suportam operações em arquivos individuais e processamento em lote de diretórios inteiros.

---

## APIs Públicas

Funções disponíveis para uso através do módulo `teletools.cipher`.

| Função | Descrição | 
|--------|-----------|
| [`encrypt_file_or_folder` 📚](cipher_api/encrypt_file_or_folder.md) | Criptografa arquivo ou todos os arquivos de uma pasta usando chave pública GPG |
| [`decrypt_file_or_folder` 📚](cipher_api/decrypt_file_or_folder.md) | Descriptografa arquivo .gpg ou todos os arquivos .gpg de uma pasta usando chave privada GPG |

---

## Documentação Relacionada

- **[Teletools](../README.md)** - Visão geral do projeto Teletools
- **[Teletools Cipher CLI](cipher_cli.md)** - Interface de linha de comando para criptografia/descriptografia

---

## Links Externos

- **[GnuPG Documentation](https://gnupg.org/documentation/)** - Documentação oficial do GNU Privacy Guard
- **[python-gnupg Documentation](https://gnupg.readthedocs.io/)** - Documentação da biblioteca python-gnupg
- **[GPG Best Practices](https://riseup.net/en/security/message-security/openpgp/best-practices)** - Melhores práticas de segurança com GPG

---

**Versão:** 0.0.2  
**Última atualização:** 2025-12-18  
**Status:** Em desenvolvimento ativo
