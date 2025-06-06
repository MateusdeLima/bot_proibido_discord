import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from services.gemini_service import GeminiService
from services.shopee_service import ShopeeService

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

gemini_service = GeminiService()
shopee_service = ShopeeService()

@bot.event
async def on_ready():
    print(f'Bot está online como {bot.user}')

@bot.command()
async def verificar(ctx, *, produto: str):
    try:
        shopee_info = await shopee_service.get_product_info(produto)
        resposta = await gemini_service.analyze_product(shopee_info)
        detalhes = resposta['details']
        if len(detalhes) > 1024:
            detalhes = detalhes[:1021] + '...'
        embed = discord.Embed(
            title="Verificação de Produto",
            description=f"Resultado da análise para: {produto}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Status", value=resposta['status'], inline=False)
        embed.add_field(name="Detalhes", value=detalhes, inline=False)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Ocorreu um erro ao verificar o produto: {str(e)}")

bot.run(os.getenv('DISCORD_TOKEN')) 