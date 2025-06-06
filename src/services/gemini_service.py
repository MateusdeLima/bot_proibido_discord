import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

class GeminiService:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def analyze_product(self, product_info):
        # Inclui apenas os trechos relevantes dos links na análise
        trechos_texto = ''
        if 'trechos_relevantes' in product_info and product_info['trechos_relevantes']:
            for url, trechos in product_info['trechos_relevantes'].items():
                for trecho in trechos:
                    trechos_texto += f'\nTrecho relevante do link {url if url != "tópico" else "tópico principal"}:\n{trecho}\n'
        else:
            trechos_texto = '\nNenhum trecho relevante encontrado nos links.'
        prompt = f"""
        Você é um especialista nas políticas da Shopee. Analise o produto abaixo e determine se ele é PROIBIDO, RESTRITO ou PERMITIDO na plataforma Shopee, seguindo as regras:
        - PROIBIDO: Não pode ser vendido de jeito nenhum na plataforma, independentemente de autorização, documento ou vendedor. Exemplo: armas de fogo, facas acima de 30cm, drogas ilícitas.
        - RESTRITO: Só pode ser vendido por alguns vendedores com autorização especial ou documento, ou em condições específicas. Exemplo: medicamentos controlados, produtos veterinários, facas de até 30cm (se permitido com restrição).
        - PERMITIDO: Pode ser vendido normalmente.

        IMPORTANTE: Leia atentamente os trechos das políticas e dos links abaixo. Se encontrar o produto listado como proibido, retorne PROIBIDO. Se encontrar como restrito, retorne RESTRITO. Sempre cite o trecho exato da política que justifica a classificação.

        Responda de forma resumida, focando nos principais pontos e respeitando o limite de 1024 caracteres para o campo de detalhes.

        Produto: {product_info['name']}
        {trechos_texto}

        Forneça uma resposta estruturada com:
        1. Status (Proibido/Restrito/Permitido)
        2. Detalhes da análise (explique o motivo e cite o trecho exato da política, de forma resumida)
        3. Referências das políticas aplicáveis (link ou citação)
        """
        response = self.model.generate_content(prompt)
        return self._format_response(response.text)

    def _format_response(self, response):
        linhas = response.split('\n')
        status = linhas[0] if linhas else 'Desconhecido'
        detalhes = '\n'.join(linhas[1:]) if len(linhas) > 1 else ''
        return {
            'status': status,
            'details': detalhes
        } 