import discord
from discord.ext import commands
import requests
import os
from dotenv import load_dotenv
from mtg_logic import MTGService 
# 1. Configuración
TOKEN = "Tu token" # Pega aquí el token que copiaste
intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix="!", intents=intents)
@bot.event
async def on_guild_join(guild):
    print(f"¡Nuevo servidor detectado! Me he unido a: {guild.name}")
    # Aquí podrías incluso enviar un log a un canal específico tuyo
@bot.event
async def on_ready():
    print(f"Bot conectado como: {bot.user}")

# 2. Comando de prueba de API (Scryfall)
@bot.command()
async def carta(ctx, *, nombre):
    datos = MTGService.buscar_carta(nombre)
    
    if datos:
        # 1. Extraer legalidades del JSON
        leg = datos.get('legalities', {})
        
        # 2. DEFINIR las variables antes de usarlas en el Embed
        # Si no se definen aquí, el 'add_field' dará error de "variable not defined"
        modern_status = "✅ Legal" if leg.get('modern') == 'legal' else "❌ No legal"
        pauper_status = "✅ Legal" if leg.get('pauper') == 'legal' else "❌ No legal"
        vintage_status = "✅ Legal" if leg.get('vintage') == 'legal' else "❌ No legal"
        commander_status = "✅ Legal" if leg.get('commander') == 'legal' else "❌ No legal"
        oathbreaker_status = "✅ Legal" if leg.get('oathbreaker') == 'legal' else "❌ No legal"

        # 3. Lógica de TEXTO (Detectar si es doble cara)
        if 'card_faces' in datos:
            # Es doble cara: iteramos para sacar nombre y texto de cada lado
            descripcion_final = ""
            for cara in datos['card_faces']:
                nombre_cara = cara.get('name', 'Cara')
                texto_cara = cara.get('oracle_text', 'Sin texto')
                coste_cara = cara.get('mana_cost', '')
                descripcion_final += f"**{nombre_cara}** {coste_cara}\n{texto_cara}\n----------------\n"
        else:
            # Es carta normal
            descripcion_final = datos.get('oracle_text', 'Sin texto.')

        # 4. Lógica de IMAGEN 
        img_frontal = None
        img_trasera = None

        if 'image_uris' in datos:
            # Caso A: Carta normal (tiene imagen en la raíz)
            img_frontal = datos['image_uris'].get('normal')
        elif 'card_faces' in datos:
            # Caso B: Carta doble cara (MDFC / Transform)
            # Cara 1 (Frontal) -> Intentamos sacarla de la primera cara
            img_frontal = datos['card_faces'][0].get('image_uris', {}).get('normal')
            
            # Cara 2 (Trasera) -> Solo si existe una segunda cara, la guardamos
            if len(datos['card_faces']) > 1:
                img_trasera = datos['card_faces'][1].get('image_uris', {}).get('normal')
        # 5. Construir Embed
        embed = discord.Embed(
            title=datos.get('name'), 
            description=descripcion_final, 
            color=discord.Color.blue()
        )
        # 6 USAR las variables definidas arriba
        embed.add_field(name="Modern", value=modern_status, inline=True)
        embed.add_field(name="Pauper", value=pauper_status, inline=True)
        embed.add_field(name="Vintage", value=vintage_status, inline=True)
        embed.add_field(name="Commander", value=commander_status, inline=True)
        embed.add_field(name="Oathbreaker", value=oathbreaker_status, inline=True)



        # 7 Asignación de imágenes al Embed 
        if img_frontal:
            embed.set_image(url=img_frontal)  # Imagen grande abajo
        
        if img_trasera:
            embed.set_thumbnail(url=img_trasera) # Imagen pequeña arriba a la derecha

        embed.set_footer(text="Datos proporcionados por Scryfall API")
        await ctx.send(embed=embed)


        embed.set_footer(text="Datos proporcionados por Scryfall API")
        await ctx.send(embed=embed)
    else:
        await ctx.send("No encontré la carta.")
class ComboPagination(discord.ui.View):
    def __init__(self, results, card_name):
        super().__init__(timeout=60)
        self.results = results
        self.card_name = card_name
        self.index = 0

    async def update_embed(self, interaction):
        variant = self.results[self.index]
        
        # Procesamiento seguro de efectos
        efectos = [e['name'] for e in variant.get('produces', []) if isinstance(e, dict) and 'name' in e]
        resultado_f = efectos[0] if efectos else "Efecto variado"
        
        instrucciones = variant.get('description', 'Sin instrucciones.')
        piezas = [u['card']['name'] for u in variant.get('uses', [])]

        embed = discord.Embed(
            title=f"Combo {self.index + 1} de {len(self.results)}",
            description=f"**Resultado:** {resultado_f}\n\n**Pasos:**\n{instrucciones}",
            color=discord.Color.gold()
        )
        embed.add_field(name="Piezas", value=" + ".join(piezas), inline=False)

        # Imagen de la primera pieza
        res_scry = requests.get(f"https://api.scryfall.com/cards/named?fuzzy={piezas[0]}")
        if res_scry.status_code == 200:
            img = res_scry.json().get('image_uris', {}).get('normal')
            if img: embed.set_thumbnail(url=img)

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Anterior", style=discord.ButtonStyle.gray)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index > 0:
            self.index -= 1
            await self.update_embed(interaction)

    @discord.ui.button(label="Siguiente", style=discord.ButtonStyle.gray)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index < len(self.results) - 1:
            self.index += 1
            await self.update_embed(interaction)

@bot.command()
async def combo(ctx, *, nombre_carta):
    # El bot le pide los datos al la pagina
    results = MTGService.buscar_combos(nombre_carta)
    
    if results:
        # Iniciamos la vista de paginación que ya tenías configurada
        view = ComboPagination(results, nombre_carta)
        
        # Preparamos el primer combo para mostrarlo de inmediato
        variant = results[0]
        piezas = " + ".join([u['card']['name'] for u in variant['uses']])
        
        embed = discord.Embed(
            title=f"Combo 1 de {len(results)}",
            description=f"**Pasos:**\n{variant.get('description', 'Sin descripción.')}",
            color=discord.Color.gold()
        )
        embed.add_field(name="Piezas", value=piezas, inline=False)
        
        await ctx.send(embed=embed, view=view)
    else:
        await ctx.send(f"No encontré combos que incluyan '{nombre_carta}'.")
bot.run(TOKEN)