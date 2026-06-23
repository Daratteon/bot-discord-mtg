import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from mtg_logic import MTGService 

# 1. Configuración de Entorno y Seguridad
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("Error crítico: No se encontró la variable DISCORD_TOKEN en el archivo mtglogic.env")

intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_guild_join(guild):
    print(f"Nuevo servidor detectado: {guild.name}")

@bot.event
async def on_ready():
    print(f"Bot conectado como: {bot.user}")

# 2. Comando principal
@bot.command()
async def carta(ctx, *, nombre):
    datos = await MTGService.buscar_carta(nombre)
    
    if not datos:
        await ctx.send("No encontré la carta.")
        return

    # 1. Extraer legalidades del JSON de forma segura
    leg = datos.get('legalities', {})
    modern_status = "✅ Legal" if leg.get('modern') == 'legal' else "❌ No legal"
    pauper_status = "✅ Legal" if leg.get('pauper') == 'legal' else "❌ No legal"
    vintage_status = "✅ Legal" if leg.get('vintage') == 'legal' else "❌ No legal"
    commander_status = "✅ Legal" if leg.get('commander') == 'legal' else "❌ No legal"
    oathbreaker_status = "✅ Legal" if leg.get('oathbreaker') == 'legal' else "❌ No legal"

    # 2. Lógica de TEXTO (Manejo seguro de listas para doble cara)
    descripcion_final = ""
    if 'card_faces' in datos and isinstance(datos['card_faces'], list):
        for cara in datos['card_faces']:
            nombre_cara = cara.get('name', 'Cara')
            texto_cara = cara.get('oracle_text', 'Sin texto')
            coste_cara = cara.get('mana_cost', '')
            descripcion_final += f"**{nombre_cara}** {coste_cara}\n{texto_cara}\n----------------\n"
    else:
        descripcion_final = datos.get('oracle_text', 'Sin texto.')

    # 3. Lógica de IMAGEN 
    img_frontal = None
    img_trasera = None

    if 'image_uris' in datos:
        img_frontal = datos['image_uris'].get('normal')
    elif 'card_faces' in datos and len(datos['card_faces']) > 0:
        img_frontal = datos['card_faces'][0].get('image_uris', {}).get('normal')
        if len(datos['card_faces']) > 1:
            img_trasera = datos['card_faces'][1].get('image_uris', {}).get('normal')

    # 4. Construir Embed
    embed = discord.Embed(
        title=datos.get('name', 'Carta Desconocida'), 
        description=descripcion_final, 
        color=discord.Color.blue()
    )
    
    embed.add_field(name="Modern", value=modern_status, inline=True)
    embed.add_field(name="Pauper", value=pauper_status, inline=True)
    embed.add_field(name="Vintage", value=vintage_status, inline=True)
    embed.add_field(name="Commander", value=commander_status, inline=True)
    embed.add_field(name="Oathbreaker", value=oathbreaker_status, inline=True)

    # 5. Asignación de imágenes al Embed 
    if img_frontal:
        embed.set_image(url=img_frontal)
    if img_trasera:
        embed.set_thumbnail(url=img_trasera)

    embed.set_footer(text="Datos proporcionados por Scryfall API")
    await ctx.send(embed=embed)


class ComboPagination(discord.ui.View):
    def __init__(self, results, card_name):
        super().__init__(timeout=60)
        self.results = results
        self.card_name = card_name
        self.index = 0

    async def update_embed(self, interaction):
        variant = self.results[self.index]
        
        # Procesamiento seguro de efectos y piezas
        efectos = [e.get('name', '') for e in variant.get('produces', []) if isinstance(e, dict)]
        resultado_f = efectos[0] if efectos else "Efecto variado"
        
        instrucciones = variant.get('description', 'Sin instrucciones.')
        piezas = [u.get('card', {}).get('name', 'Carta') for u in variant.get('uses', []) if isinstance(u, dict)]

        embed = discord.Embed(
            title=f"Combo {self.index + 1} de {len(self.results)}",
            description=f"**Resultado:** {resultado_f}\n\n**Pasos:**\n{instrucciones}",
            color=discord.Color.gold()
        )
        embed.add_field(name="Piezas", value=" + ".join(piezas) if piezas else "N/A", inline=False)

        # Delegación segura de la petición a MTGService
        if piezas:
            data_scry = await MTGService.buscar_carta(piezas[0])
            if data_scry:
                img = data_scry.get('image_uris', {}).get('normal')
                if not img and 'card_faces' in data_scry and len(data_scry['card_faces']) > 0:
                    img = data_scry['card_faces'][0].get('image_uris', {}).get('normal')
                
                if img: 
                    embed.set_thumbnail(url=img)

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
    results = await MTGService.buscar_combos(nombre_carta)
    
    if results:
        view = ComboPagination(results, nombre_carta)
        variant = results[0]
        
        piezas = [u.get('card', {}).get('name', 'Carta') for u in variant.get('uses', []) if isinstance(u, dict)]
        
        embed = discord.Embed(
            title=f"Combo 1 de {len(results)}",
            description=f"**Pasos:**\n{variant.get('description', 'Sin descripción.')}",
            color=discord.Color.gold()
        )
        embed.add_field(name="Piezas", value=" + ".join(piezas) if piezas else "N/A", inline=False)
        
        await ctx.send(embed=embed, view=view)
    else:
        await ctx.send(f"No encontré combos que incluyan '{nombre_carta}'.")

if __name__ == "__main__":
    bot.run(TOKEN)