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

@bot.event
async def on_ready():
    print(f"✅ Бот {bot.user} запущено!")

@bot.command(name="активність")
async def активність(ctx, *, args):
    try:
        await ctx.message.delete()

        частини = args.split("|")

        if len(частини) < 2:
            await ctx.send("❌ Формат:\nЗ описом: !активність Назва | Опис | Дата`\nБез опису: !активність Назва | Дата`", delete_after=10)
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

        учасники = {
            "👍🏻": [],
            "❓": [],
            "👎🏻": []
        }

        timestamp = int(час_utc.timestamp())

        embed = discord.Embed(
            title=f"📢 {назва}",
            color=0x00ff00
        )

        if опис:
            embed.description = f"{опис}\n\n📅 <t:{timestamp}:F> (<t:{timestamp}:R>)"
        else:
            embed.description = f"📅 <t:{timestamp}:F> (<t:{timestamp}:R>)"

        for emoji in учасники:
            embed.add_field(name=f"{emoji} (0)", value="Ніхто", inline=True)

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

    if message_id not in reaction_data or emoji not in ["👍🏻", "❓", "👎🏻"]:
        return

    дані = reaction_data[message_id]
    учасники = дані["учасники"]

    for інше_емоджі in ["👍🏻", "❓", "👎🏻"]:
        if user.mention in учасники[інше_емоджі]:
            учасники[інше_емоджі].remove(user.mention)

    if user.mention not in учасники[emoji]:
        учасники[emoji].append(user.mention)

    try:
        await reaction.message.remove_reaction(emoji, user)
    except:
        pass

    await оновити_embed(reaction.message, дані)

async def оновити_embed(повідомлення, дані):
    старий = повідомлення.embeds[0]
    новий = discord.Embed(
        title=старий.title,
        description=старий.description,
        color=старий.color
    )

    учасники = дані["учасники"]

    for emoji in ["👍🏻", "❓", "👎🏻"]:
        список = "\n".join(учасники[emoji]) if учасники[emoji] else "Ніхто"
        кількість = len(учасники[emoji])
        новий.add_field(name=f"{emoji} ({кількість})", value=список, inline=True)

    await повідомлення.edit(embed=новий)

@bot.command(name="твіни")
async def твіни(ctx):
    await ctx.message.delete()

    твіни = {
        "1️⃣": "Твін 1",
        "2️⃣": "Твін 2",
        "3️⃣": "Твін 3",
        "4️⃣": "Твін 4",
        "5️⃣": "Твін 5",
        "6️⃣": "Твін 6",
        "7️⃣": "Твін 7",
        "8️⃣": "Твін 8",
        "9️⃣": "Твін 9"
    }

    вибори = {key: [] for key in твіни}
    додаткові = ["❌", "🔁"]

    embed = discord.Embed(
        title="🧬 Обери свого Твіна",
        color=0x3498db
    )

    for emoji, name in твіни.items():
        embed.add_field(name=f"{emoji} {name}", value="Ніхто", inline=False)

    msg = await ctx.send(embed=embed)

    twin_data = {
        "message": msg,
        "твіни": твіни,
        "вибори": вибори
    }

    bot.twin_data = bot.twin_data if hasattr(bot, "twin_data") else {}
    bot.twin_data[msg.id] = twin_data

    for emoji in list(твіни.keys()) + додаткові:
        await msg.add_reaction(emoji)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    msg_id = reaction.message.id
    emoji = str(reaction.emoji)

    if not hasattr(bot, "twin_data") or msg_id not in bot.twin_data:
        return

    data = bot.twin_data[msg_id]
    твіни = data["твіни"]
    вибори = data["вибори"]

    if emoji == "❌":
        for список in вибори.values():
            if user.mention in список:
                список.remove(user.mention)
        await оновити_твіни(reaction.message, data)
        await reaction.message.remove_reaction(emoji, user)
        return

    if emoji == "🔁":
        await оновити_твіни(reaction.message, data)
        await reaction.message.remove_reaction(emoji, user)
        return

    if emoji in твіни:
        for список in вибори.values():
            if user.mention in список:
                список.remove(user.mention)

        вибори[emoji].append(user.mention)
        await оновити_твіни(reaction.message, data)
        await reaction.message.remove_reaction(emoji, user)

async def оновити_твіни(msg, data):
    embed = discord.Embed(
        title="🧬 Обери свого Твіна",
        color=0x3498db
    )

    for emoji, name in data["твіни"].items():
        учасники = data["вибори"][emoji]
        текст = "\n".join(учасники) if учасники else "Ніхто"
        embed.add_field(name=f"{emoji} {name}", value=текст, inline=False)

    await msg.edit(embed=embed)

keep_alive()
bot.run(os.getenv("TOKEN"))
