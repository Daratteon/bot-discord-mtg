# Magic: The Gathering Discord Bot 🃏

Este es un bot de Discord desarrollado en **Python** que integra la API de **Scryfall** y **Commander Spellbook** para proporcionar herramientas útiles a jugadores de MTG. 

## 🚀 Funcionalidades
- **Búsqueda de cartas:** Obtiene información actualizada de cualquier carta de Magic, incluyendo su legalidad en formatos como Pauper, Commander y Modern.
- **Soporte para Doble Cara:** Visualización completa de cartas transformables y modales (MDFCs), mostrando ambas caras en un solo mensaje.
- **Buscador de Combos:** Integración con la API de Commander Spellbook para listar combos legales que incluyen una carta específica.
- **Interfaz Interactiva:** Uso de botones de Discord para navegar por múltiples resultados de combos.

## 🛠️ Tecnologías utilizadas
- **Lenguaje:** Python 3.x
- **Librería principal:** `discord.py`
- **Peticiones HTTP:** `aiohttp` (Arquitectura asíncrona para evitar bloqueos del bot).
- **APIs externas:** Scryfall API y Commander Spellbook API.
- **Gestión de entorno:** `python-dotenv` para seguridad de tokens.

## 📦 Instalación y Configuración

1. Clona el repositorio.
2. Crea un archivo `.env` en la raíz del proyecto.
3. Agrega tu token de Discord: `DISCORD_TOKEN=tu_token_aqui`
4. Instala las dependencias asíncronas: 
    ```bash
    pip install discord.py aiohttp python-dotenv
    ```