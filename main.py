from keep_alive import keep_alive
import discord
from discord.ext import commands
import datetime
import pytz
import asyncio
import os

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

reaction_data = {}
twin_data = {}

@bot.event
async def on_ready():
    print(f"✅ Бот {bot.user} запущено!")

@bot.command(name="активність")
async def активність(ctx, *, args):
    try:
        await ctx.message.delete()
        частини = args.split("|")

        if len(частини) < 2:
            await ctx.send("❌ Формат:\nЗ описом: !активність Назва | Опис | Дата\nБез опису: !активність Назва | Дата", delete_after=10)
            return

        назва = частини[0].strip()
        if len(частини) == 2:
            опис = ""
            дата_час = частини[1].strip()
            таймзона = "Europe/Kyiv"
        elif len(частини) >= 3:
            опис = частини[1].strip()
            дата_час = частини[2].strip()
            таймзона = частини[3].strip() if len(частини) >= 4 else "Europe/Kyiv"
        else:
            await ctx.send("❌ Неправильний формат команди.", delete_after=5)
            return

        dt = datetime.datetime.strptime(дата_час, "%Y-%m-%d %H:%M")
        локальна_таймзона = pytz.timezone(таймзона)
        локальний_час = локальна_таймзона.localize(dt)
        час_utc = локальний_час.astimezone(pytz.utc)
        зараз = datetime.datetime.now(pytz.utc)
        залишилось = час_utc - зараз

        if залишилось.total_seconds() <= 0:
            await ctx.send("❌ Вказана дата/час уже минули.", delete_after=5)
            return

        учасники = {"👍🏻": [], "❓": [], "👎🏻": []}
        timestamp = int(час_utc.timestamp())
        embed = discord.Embed(title=f"📢 {назва}", color=0x00ff00)
        if опис:
            embed.description = f"{опис}\n\n📅 <t:{timestamp}:F> (<t:{timestamp}:R>)"
        else:
            embed.description = f"📅 <t:{timestamp}:F> (<t:{timestamp}:R>)"

        for emoji in учасники:
            embed.add_field(name=f"{emoji} (0)", value="—", inline=True)

        повідомлення = await ctx.send(embed=embed)

        reaction_data[повідомлення.id] = {
            "message": повідомлення,
            "учасники": учасники
        }

        for emoji in учасники:
            await повідомлення.add_reaction(emoji)

        await asyncio.sleep(залишилось.total_seconds())
        await повідомлення.delete()

    except Exception as e:
        await ctx.send(f"⚠️ Помилка: {e}", delete_after=8)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    message_id = reaction.message.id
    emoji = str(reaction.emoji)

    if message_id in reaction_data and emoji in reaction_data[message_id]["учасники"]:
        дані = reaction_data[message_id]
        учасники = дані["учасники"]

        for інше_емоджі in учасники:
            if user.mention in учасники[інше_емоджі]:
                учасники[інше_емоджі].remove(user.mention)

        учасники[emoji].append(user.mention)

        try:
            await reaction.message.remove_reaction(emoji, user)
        except:
            pass

        await оновити_активність_embed(reaction.message, дані)

    elif message_id in twin_data:
        дані = twin_data[message_id]
        if emoji == "🔁":
            for ключ in дані["твін_власники"]:
                дані["твін_власники"][ключ] = None
            await оновити_twin_embed(reaction.message, дані)
        elif emoji == "❌":
            for ключ, власник in дані["твін_власники"].items():
                if власник == user.mention:
                    дані["твін_власники"][ключ] = None
            await оновити_twin_embed(reaction.message, дані)
        elif emoji in дані["твін_власники"]:
            # Якщо Твін уже зайнятий — не даємо обрати
            if дані["твін_власники"][emoji] is None:
                # Забираємо попереднього Твіна, якщо обирав
                for ключ in дані["твін_власники"]:

if дані["твін_власники"][ключ] == user.mention:
                        дані["твін_власники"][ключ] = None
                дані["твін_власники"][emoji] = user.mention
                await оновити_twin_embed(reaction.message, дані)
        try:
            await reaction.message.remove_reaction(emoji, user)
        except:
            pass

async def оновити_активність_embed(повідомлення, дані):
    старий = повідомлення.embeds[0]
    новий = discord.Embed(title=старий.title, description=старий.description, color=старий.color)
    учасники = дані["учасники"]

    for emoji in учасники:
        список = " — ".join(учасники[emoji]) if учасники[emoji] else "—"
        кількість = len(учасники[emoji])
        новий.add_field(name=f"{emoji} ({кількість})", value=список, inline=True)

    await повідомлення.edit(embed=новий)

@bot.command(name="твін")
async def твін(ctx):
    твіни = {
        "1️⃣": "Твін 1", "2️⃣": "Твін 2", "3️⃣": "Твін 3",
        "4️⃣": "Твін 4", "5️⃣": "Твін 5", "6️⃣": "Твін 6",
        "7️⃣": "Твін 7", "8️⃣": "Твін 8", "9️⃣": "Твін 9"
    }

    власники = {ключ: None for ключ in твіни}

    embed = discord.Embed(title="👥 Обери свого Твіна", color=0x3498db)
    for emoji, твін in твіни.items():
        embed.add_field(name=f"{emoji} {твін}", value="—", inline=True)

    повідомлення = await ctx.send(embed=embed)

    twin_data[повідомлення.id] = {
        "message": повідомлення,
        "твін_власники": власники,
        "твіни": твіни
    }

    for emoji in твіни:
        await повідомлення.add_reaction(emoji)

    await повідомлення.add_reaction("❌")
    await повідомлення.add_reaction("🔁")

async def оновити_twin_embed(повідомлення, дані):
    embed = discord.Embed(title="👥 Обери свого Твіна", color=0x3498db)

    for emoji, твін in дані["твіни"].items():
        власник = дані["твін_власники"][emoji]
        embed.add_field(
            name=f"{emoji} {твін}",
            value=власник if власник else "—",
            inline=True
        )

    await повідомлення.edit(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, кількість: int = 5):
    await ctx.channel.purge(limit=кількість + 1)
    повідомлення = await ctx.send(f"🧹 Очищено {кількість} повідомлень.")
    await asyncio.sleep(3)
    await повідомлення.delete()

keep_alive()
bot.run(os.getenv("TOKEN"))
