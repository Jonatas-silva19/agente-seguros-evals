# Agente de Seguros com Tool Calling e Auditoria Automatizada (LLM Evals)

Protótipo de agente conversacional desenvolvido em Python com o SDK oficial `google-genai`, focado em **mercados regulados (Seguros)** onde a precisão factual e a mitigação de alucinações são críticas.

## Arquitetura do Projeto

1. **Tool Calling Determinístico (`consultar_apolice`)**: O agente não depende da memória paramétrica do LLM para dados cadastrais. Toda consulta de cobertura, franquia ou status exige chamada explícita à função de consulta com validação de esquema via *type hints* e *docstrings*.
2. **Resiliência e Tratamento de Falhas (`chamar_com_retentativa`)**: Implementação de retentativas automáticas para lidar com erros transitórios de infraestrutura (`503 UNAVAILABLE`).
3. **Avaliador Automatizado / LLM-as-a-Judge (`avaliar_resposta_agente`)**: Pipeline de auditoria pós-geração (`temperature=0.0` e saída estruturada em JSON) que compara a resposta do agente contra um *Ground Truth* para detectar alucinações e desvios factuais antes da entrega.

## Como Executar

```bash
pip install -r requirements.txt
export GEMINI_API_KEY="sua_chave_aqui" # No PowerShell: $env:GEMINI_API_KEY="sua_chave_aqui"
python agente_seguros.py
