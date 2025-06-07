import google.generativeai as genai
import os
from dotenv import load_dotenv
import unicodedata

load_dotenv()

class GeminiService:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def _normalize(self, text):
        return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII').lower()

    def _buscar_trechos_politicas(self, termo):
        # Lista de sinônimos e palavras relacionadas para melhorar a busca
        sinonimos = [termo]
        termo_norm = self._normalize(termo)
        # Regras específicas para óculos
        if termo_norm in ["oculos de grau", "oculos com grau", "oculos", "armação de oculos", "armações de oculos", "armação", "armações"]:
            sinonimos += [
                "oculos de grau", "oculos com grau", "oculos", "armação de oculos", "armações de oculos", "armação", "armações"
            ]
        # Regras específicas para facas e lâminas
        if "faca" in termo_norm or "lâmina" in termo_norm or "lamina" in termo_norm:
            sinonimos += [
                "faca", "facas", "lâmina", "lamina", "lâminas", "laminas", "faca de cozinha", "facas de cozinha", "faca de acampamento", "faca de sobrevivência", "faca longa", "faca tradicional", "faca cerimonial", "faca de cinto", "faca escondida", "lâmina maior que 30 centímetros", "lâmina menor que 30 centímetros"
            ]
        # Regras específicas para animais
        if "animal" in termo_norm or "galinha" in termo_norm or "galo" in termo_norm or "cachorro" in termo_norm or "gato" in termo_norm or "ser vivo" in termo_norm:
            sinonimos += [
                "animal", "animais", "animal doméstico", "animais domésticos", "animal silvestre", "animais silvestres", "animal de criação", "animais de criação", "ser vivo", "seres vivos", "galinha", "galo", "cachorro", "gato", "partes de seres vivos", "produtos de animal", "produtos de animais", "produtos provindos de animais"
            ]
        # Adicione outros casos específicos conforme necessário
        try:
            with open('Politicas Proibidos - Shopee.txt', 'r', encoding='utf-8') as f:
                texto = f.read()
            texto_norm = self._normalize(texto)
            trechos = []
            for termo_s in sinonimos:
                termo_s_norm = self._normalize(termo_s)
                idx = 0
                while True:
                    idx = texto_norm.find(termo_s_norm, idx)
                    if idx == -1:
                        break
                    # Ampliar o contexto: 400 caracteres antes e depois
                    start = max(0, idx - 400)
                    end = min(len(texto), idx + 400)
                    trecho = texto[start:end].replace('\n', ' ')
                    trechos.append(trecho)
                    idx += len(termo_s_norm)
            return trechos if trechos else ['Nenhum trecho relevante encontrado no arquivo de políticas.']
        except Exception as e:
            return [f'Não foi possível ler o arquivo de políticas: {e}']

    async def analyze_product(self, product_info):
        trechos_texto = ''
        if 'trechos_relevantes' in product_info and product_info['trechos_relevantes']:
            for url, trechos in product_info['trechos_relevantes'].items():
                for trecho in trechos:
                    trechos_texto += f'\nTrecho relevante do link {url if url != "tópico" else "tópico principal"}:\n{trecho}\n'
        else:
            trechos_texto = '\nNenhum trecho relevante encontrado nos links.'
        trechos_politicas = self._buscar_trechos_politicas(product_info['name'])
        trechos_politicas_txt = '\n'.join(trechos_politicas)
        prompt = f"""
        Você é um especialista nas políticas da Shopee. Analise o produto abaixo e determine se ele é PROIBIDO, RESTRITO ou PERMITIDO na plataforma Shopee, seguindo as regras:
        - PROIBIDO: Não pode ser vendido de jeito nenhum na plataforma. Se não houver menção de que pode ser vendido com autorização ou documento, considere como proibido.
        - RESTRITO: Só pode ser vendido se houver menção explícita de que é permitido vender com autorização especial, licença ou documento. Se não houver essa menção, não considere como restrito.
        - PERMITIDO: Pode ser vendido normalmente. Se não houver menção ao produto nas políticas, ou se houver menção clara de permissão, considere como permitido.

        ATENÇÃO: Considere como PROIBIDOS todos os produtos que sejam usados, reembalados, fracionados, testados, abertos ou similares, mesmo que não haja menção direta ao termo exato do produto nas políticas. Por exemplo, perfumes fracionados devem ser considerados como perfumes usados, que são proibidos. O mesmo vale para qualquer cosmético ou produto de uso pessoal nessas condições.

        REGRA PARA FACAS E LÂMINAS: Facas e lâminas com área de corte maior que 30 centímetros (12 polegadas) são proibidas. Facas e lâminas com área de corte igual ou menor que 30 centímetros são permitidas, exceto se houver outra restrição específica. Sempre diferencie pelo tamanho da lâmina.

        REGRA PARA ANIMAIS: É proibida a venda de qualquer animal vivo, parte de animal, ou produto proveniente de animal silvestre, doméstico ou de criação, mesmo que não haja menção direta ao termo exato do animal. Isso inclui galinhas, galos, cachorros, gatos, etc.

        IMPORTANTE: Faça uma análise criteriosa dos trechos das políticas e dos links abaixo, bem como dos trechos extraídos do arquivo de políticas proibidas da Shopee (abaixo). Só classifique como restrito se houver menção clara de venda com autorização, licença ou documento. Caso contrário, se houver qualquer proibição, classifique como proibido. Sempre cite o trecho exato da política que justifica a classificação.

        Produto: {product_info['name']}
        Trechos do site:
        {trechos_texto}

        Trechos relevantes do arquivo de políticas proibidas:
        {trechos_politicas_txt}

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