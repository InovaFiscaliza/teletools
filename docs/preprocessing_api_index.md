> **[← Voltar para Teletools](../README.md)**

# Teletools Preprocessing API

Índice de referência das APIs públicas do módulo `teletools.preprocessing`.

---

## Visão Geral

O módulo `teletools.preprocessing` fornece funções para normalização e validação de números telefônicos brasileiros de acordo com os planos de numeração da ANATEL (Agência Nacional de Telecomunicações) e o padrão internacional ITU-T E.164.

O módulo processa diversos formatos de números brasileiros incluindo:
- **SMP** (Serviço Móvel Pessoal) - Serviços móveis
- **STFC** (Serviço Telefônico Fixo Comutado) - Linhas fixas
- **SME** (Serviço Móvel Especializado) - Móveis especializados
- **SUP** (Serviço de Utilidade Pública) - Serviços de utilidade pública
- **CNG** (Código Nacional de Gratuidade) - Códigos de chamadas gratuitas (0800, 0300, etc.)

---

## APIs Públicas

Funções disponíveis para uso através do módulo `teletools.preprocessing`.

| Função | Descrição | 
|--------|-----------|
| [`normalize_number` 📚](preprocessing_api/normalize_number.md) | Normaliza um único número telefônico brasileiro segundo os padrões ANATEL |
| [`normalize_number_pair` 📚](preprocessing_api/normalize_number_pair.md) | Normaliza um par de números telefônicos relacionados com inferência contextual de código de área |

---

## Documentação Relacionada

- **[Teletools](../README.md)** - Visão geral do projeto Teletools
- **[Teletools Database API](database_api_index.md)** - APIs para consulta de dados de telecomunicações
- **[Teletools ABR Loader](abr_loader.md)** - Cliente para importação de dados da ABR Telecom

---

## Links Externos

- **[ANATEL - Plano de Numeração](https://www.anatel.gov.br/)** - Planos de numeração oficiais da ANATEL
- **[ITU-T E.164 Standard](https://handle.itu.int/11.1002/1000/10688)** - Padrão internacional de numeração telefônica

---

**Versão:** 0.0.2  
**Última atualização:** 2025-12-18  
**Status:** Em desenvolvimento ativo
