import requests

class MTGService:
    @staticmethod
    def buscar_carta(nombre):
        url = f"https://api.scryfall.com/cards/named?fuzzy={nombre.replace(' ', '+')}"
        res = requests.get(url)
        return res.json() if res.status_code == 200 else None

    @staticmethod
    def buscar_combos(nombre_carta):
        # Limpiamos el nombre para la URL del backend de Spellbook
        query = nombre_carta.replace(' ', '%20')
        url = f"https://backend.commanderspellbook.com/variants?q=card%3A%22{query}%22"
        res = requests.get(url)
        if res.status_code == 200:
            return res.json().get('results', [])
        return []