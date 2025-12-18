> **[← Voltar para Teletools](../README.md)**

# Teletools Database API

Índice de referência das APIs públicas do módulo `teletools.database`.

---

## Visão Geral

O módulo `teletools.database` fornece interface Python de alto nível para consulta de dados de telecomunicações brasileiras da ABR Telecom (Associação Brasileira de Recursos em Telecomunicações). As APIs permitem consultar informações de operadoras, status de portabilidade e dados do plano de numeração a partir de um banco de dados PostgreSQL otimizado.

---

## APIs Públicas

Funções disponíveis para uso através do módulo `teletools.database`.

| Função | Descrição | 
|--------|-----------|
| [`query_numbers_carriers` 📚](database_api/query_numbers_carriers.md)| Consulta informações de operadora e status de portabilidade para números telefônicos brasileiros |

---

## Documentação Relacionada

- **[Teletools](../README.md)** - Visão geral do projeto Teletools
- **[Teletools ABR Loader](abr_loader.md)** - Cliente para importação de dados da ABR Telecom
- **[Teletools CDR Stage Database](cdr_stage.md)** - Configuração do banco de dados PostgreSQL


---

## Links Externos

- **[ABR Telecom NSAPN](https://easi.abrtelecom.com.br/nsapn/)** - Portal oficial de dados de numeração
- **[PostgreSQL Documentation](https://www.postgresql.org/docs/)** - Documentação do PostgreSQL
- **[pandas Documentation](https://pandas.pydata.org/docs/)** - Documentação do pandas

---

**Versão:** 0.0.2  
**Última atualização:** 2025-12-17  
**Status:** Em desenvolvimento ativo
