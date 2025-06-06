import requests
from bs4 import BeautifulSoup
import unicodedata

class ShopeeService:
    def __init__(self):
        self.base_url = "https://seller.shopee.com.br/edu/article/3304/politica-de-produtos-proibidos-e-restritos"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

    def normalize(self, text):
        return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII').lower()

    async def get_product_info(self, product_name):
        response = requests.get(self.base_url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        produto_lower = self.normalize(product_name)
        # Procurar todos os links "clique aqui" na página
        topicos = []
        for a in soup.find_all('a', string=lambda s: s and 'clique aqui' in self.normalize(s)):
            href = a.get('href')
            if href and href.startswith('http'):
                link = href
            elif href:
                link = 'https://seller.shopee.com.br' + href
            else:
                link = None
            texto = a.parent.get_text(separator=' ', strip=True) if a.parent else ''
            topicos.append({'texto': texto, 'link': link})
        # Busca o produto no texto dos links
        trechos_relevantes = {}
        for topico in topicos:
            if topico['link']:
                try:
                    r = requests.get(topico['link'], timeout=10, headers=self.headers)
                    s = BeautifulSoup(r.text, 'html.parser')
                    texto_link = s.get_text(separator=' ', strip=True)
                    texto_link_normalizado = self.normalize(texto_link)
                    trechos = []
                    idx = 0
                    while True:
                        idx = texto_link_normalizado.find(produto_lower, idx)
                        if idx == -1:
                            break
                        start = max(0, idx - 100)
                        end = min(len(texto_link), idx + 100)
                        trecho = texto_link[start:end].replace('\n', ' ')
                        trechos.append(trecho)
                        idx += len(produto_lower)
                    if trechos:
                        trechos_relevantes[topico['link']] = trechos
                except Exception as e:
                    trechos_relevantes[topico['link']] = [f'Erro ao acessar: {e}']
        # Se não encontrou em links, retorna o contexto do tópico
        if not trechos_relevantes and topicos:
            for topico in topicos:
                trechos_relevantes['tópico'] = [topico['texto']]
        return {
            'name': product_name,
            'category': 'Categoria desconhecida',
            'details': 'Sem detalhes adicionais.',
            'topicos': topicos,
            'trechos_relevantes': trechos_relevantes
        } 