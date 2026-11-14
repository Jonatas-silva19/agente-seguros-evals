﻿import os
import time
import json
from google import genai
from google.genai import types
from google.genai.errors import ServerError

client = genai.Client()

APOLICES_DB = {
    "AP-1020": {
        "cliente": "Carlos Silva",
        "tipo": "Seguro Auto",
        "status": "Ativa",
        "cobertura_vidros": True,
        "franquia_reais": 2500.00,
        "assistencia_24h": "Ilimitada até 400km"
    },
    "AP-3040": {
        "cliente": "Mariana Souza",
        "tipo": "Seguro Residencial",
        "status": "Pendente de Pagamento",
        "cobertura_vidros": False,
        "franquia_reais": 800.00,
        "assistencia_24h": "Chaveiro e encanador (até 2 acionamentos/ano)"
    }
}

def consultar_apolice(numero_apolice: str) -> str:
    """Consulta os detalhes, status e coberturas de uma apólice de seguro pelo número.

    Args:
        numero_apolice: O código identificador da apólice (ex: 'AP-1020').
    """
    codigo = numero_apolice.strip().upper()
    apolice = APOLICES_DB.get(codigo)
    if not apolice:
        return json.dumps({"erro": f"Apólice {codigo} não encontrada no sistema."}, ensure_ascii=False)
    return json.dumps({"numero_apolice": codigo, **apolice}, ensure_ascii=False)

def chamar_com_retentativa(funcao, tentativas=3):
    for tentativa in range(tentativas):
        try:
            return funcao()
        except ServerError:
            if tentativa == tentativas - 1:
                raise
            time.sleep(4)

def executar_agente(pergunta_usuario: str) -> str:
    instrucao_sistema = (
        "Você é um agente de atendimento especializado em seguros. "
        "Sempre utilize a ferramenta 'consultar_apolice' antes de responder sobre dados de clientes. "
        "Nunca invente coberturas ou valores que não estejam explicitamente retornados pela ferramenta. "
        "Se a apólice não existir, informe educadamente ao cliente."
    )

    response = chamar_com_retentativa(lambda: client.models.generate_content(
        model="gemini-4-hydrogen",
        contents=pergunta_usuario,
        config=types.GenerateContentConfig(
            system_instruction=instrucao_sistema,
            tools=[consultar_apolice],
            temperature=0.1,
        ),
    ))
    return response.text

def avaliar_resposta_agente(pergunta: str, resposta_agente: str, contexto_esperado: str) -> dict:
    """Audita a resposta do agente verificando fidelidade aos fatos e ausência de alucinação."""
    prompt_auditoria = f"""
    Você é um auditor técnico de qualidade de IA (LLM Evals).
    Avalie se a resposta do agente é 100% fiel ao contexto esperado, sem alucinações.

    Pergunta do usuário: {pergunta}
    Fatos verdadeiros (Ground Truth): {contexto_esperado}
    Resposta gerada pelo agente: {resposta_agente}

    Retorne APENAS um JSON válido com as chaves:
    - "aprovado" (booleano)
    - "alucinacao_detectada" (booleano)
    - "justificativa" (string curta explicando o motivo)
    """

    eval_response = chamar_com_retentativa(lambda: client.models.generate_content(
        model="gemini-4-hydrogen",
        contents=prompt_auditoria,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.0,
        ),
    ))
    return json.loads(eval_response.text)

if __name__ == "__main__":
    if not os.getenv("GEMINI_API_KEY"):
        print("ERRO: Defina a variável de ambiente GEMINI_API_KEY antes de rodar.")
        exit(1)

    casos_de_teste = [
        {
            "pergunta": "Olá, gostaria de saber se minha apólice AP-1020 cobre troca de para-brisa e qual o valor da franquia.",
            "ground_truth": "Cliente Carlos Silva, Seguro Auto Ativo, cobertura de vidros é True (sim), franquia de R$ 2.500,00."
        },
        {
            "pergunta": "Tenho a apólice AP-3040. Posso acionar o guincho agora?",
            "ground_truth": "Cliente Mariana Souza, Apólice AP-3040 é Seguro Residencial (não cobre guincho auto), está Pendente de Pagamento, assistência é apenas chaveiro e encanador (até 2 acionamentos/ano)."
        },
        {
            "pergunta": "Qual o status da apólice AP-9999?",
            "ground_truth": "Apólice AP-9999 não existe no sistema."
        }
    ]

    for i, caso in enumerate(casos_de_teste, 1):
        print(f"\n--- Teste {i} ---")
        print(f"Usuário: {caso['pergunta']}")
        resposta = executar_agente(caso["pergunta"])
        print(f"Agente:  {resposta}")

        auditoria = avaliar_resposta_agente(caso["pergunta"], resposta, caso["ground_truth"])
        print(f"Auditoria (Eval): {auditoria}")
        time.sleep(3)
        