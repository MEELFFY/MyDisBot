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
            await ctx.send("❌ Формат:\nЗ описом: `!активність Назва | Опис | Дата`\nБез опису: `!активність Назва | Дата`", delete_after=10)
            return

        назва = частини[0].strip()
        if len(частини) == 2:
            опис = ""
            дата_час = частини[1].strip()
        else:
            опис = частини[1].strip()
            дата_час = частини[2].strip()

        dt = datetime.datetime.strptime(дата_час, "%Y-%m-%d %H:%M")
        локальна_таймзона = pytz.timezone("Europe/Kyiv")
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
        опис_embed = f"{опис}\n\n📅 <t:{timestamp}:F> (<t:{timestamp}:R>)" if опис else f"📅 <t:{timestamp}:F> (<t:{timestamp}:R>)"
        embed.description = опис_embed

        for emoji in учасники:
            embed.add_field(name=f"{emoji} (0)", value="Ніхто", inline=True)

        повідомлення = await ctx.send(embed=embed)
        reaction_data[повідомлення.id] = {"message": повідомлення, "учасники": учасники}

        for emoji in учасники:
            await повідомлення.add_reaction(emoji)

        await asyncio.sleep(залишилось.total_seconds())
        await повідомлення.delete()

    except Exception as e:
        await ctx.send(f"⚠️ Помилка: {e}", delete_after=8)

async def оновити_embed(повідомлення, дані):
    старий = повідомлення.embeds[0]
    новий = discord.Embed(title=старий.title, description=старий.description, color=старий.color)
    учасники = дані["учасники"]

    for emoji in ["👍🏻", "❓", "👎🏻"]:
        список = "\n".join(учасники[emoji]) if учасники[emoji] else "Ніхто"
        кількість = len(учасники[emoji])
        новий.add_field(name=f"{emoji} ({кількість})", value=список, inline=True)

    await повідомлення.edit(embed=новий)

@bot.command(name="твін")
async def твін(ctx):
    await ctx.message.delete()

    твіни = [f"Твін {i}" for i in range(1, 10)]
    emojis = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣']
    emoji_map = dict(zip(emojis, твіни))
    дані = {твін: None for твін in твіни}

    embed = discord.Embed(title="🌀 Обери свого Твіна", color=0x0099ff)
    for твін in твіни:
        учасник = дані[твін]
        embed.add_field(name="\u200b", value=f"**{твін}** - {учасник or ''}", inline=False)

    повідомлення = await ctx.send(embed=embed)
    bot.twin_messages = getattr(bot, "twin_messages", {})
    bot.twin_messages[повідомлення.id] = {"message": повідомлення, "дані": дані, "emoji_map": emoji_map}

    for emoji in emojis + ['❌', '🔁']:
        await повідомлення.add_reaction(emoji)

@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    message_id = reaction.message.id
    emoji = str(reaction.emoji)

    if message_id in reaction_data and emoji in ["👍🏻", "❓", "👎🏻"]:
        дані = reaction_data[message_id]
        учасники = дані["учасники"]

        for інше in ["👍🏻", "❓", "👎🏻"]:
            if user.mention in учасники[інше]:
                учасники[інше].remove(user.mention)

        учасники[emoji].append(user.mention)

        try:
            await reaction.message.remove_reaction(emoji, user)
        except:
            pass

        await оновити_embed(reaction.message, дані)
        return

    if hasattr(bot, "twin_messages") and message_id in bot.twin_messages:
        twin_data = bot.twin_messages[message_id]
        дані = twin_data["дані"]
        emoji_map = twin_data["emoji_map"]

        if emoji == '🔁':
            for ключ in дані:
                дані[ключ] = None
        elif emoji == '❌':
            for ключ in дані:
                if дані[ключ] == user.mention:
                    дані[ключ] = None
        elif emoji in emoji_map:
            вибраний = emoji_map[emoji]
            for ключ in дані:
                if дані[ключ] == user.mention:
                    дані[ключ] = None
            дані[вибраний] = user.mention

        новий_embed = discord.Embed(title="🌀 Обери свого Твіна", color=0x0099ff)
        for твін in дані:
            учасник = дані[твін]
            новий_embed.add_field(name="\u200b", value=f"**{твін}** - {учасник or ''}", inline=False)

        await reaction.message.edit(embed=новий_embed)

        try:
            await reaction.message.remove_reaction(emoji, user)
        except:
            pass

# Підтримка безперервної роботи
keep_alive()

# 🔒 Запуск з середовища — тільки TOKEN!
bot.run(os.getenv("TOKEN"))