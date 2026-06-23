import aiohttp
import urllib.parse

class MTGService:
    # Definición de cabeceras requeridas por las políticas de la API
    HEADERS = {
        'User-Agent': 'MiBotDiscordMTG/1.0',
        'Accept': 'application/json'
    }

    @staticmethod
    async def buscar_carta(nombre):
        # Sanitización de entrada
        query_segura = urllib.parse.quote(nombre)
        url = f"https://api.scryfall.com/cards/named?fuzzy={query_segura}"
        
        async with aiohttp.ClientSession(headers=MTGService.HEADERS) as session:
            try:
                async with session.get(url) as res:
                    if res.status == 200:
                        return await res.json()
                    return None
            except aiohttp.ClientError as e:
                # Captura de errores de red para evitar caída de la tarea
                print(f"Error de conexión HTTP en buscar_carta: {e}")
                return None

    @staticmethod
    async def buscar_combos(nombre_carta):
        # Sanitización de entrada
        query_segura = urllib.parse.quote(nombre_carta)
        url = f"https://backend.commanderspellbook.com/variants?q=card%3A%22{query_segura}%22"
        
        async with aiohttp.ClientSession(headers=MTGService.HEADERS) as session:
            try:
                async with session.get(url) as res:
                    if res.status == 200:
                        data = await res.json()
                        return data.get('results', [])
                    return []
            except aiohttp.ClientError as e:
                # Captura de errores de red para evitar caída de la tarea
                print(f"Error de conexión HTTP en buscar_combos: {e}")
                return []