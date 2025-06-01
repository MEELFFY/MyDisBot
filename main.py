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

@bot.command(name="твін")
async def твін(ctx):
    await ctx.message.delete()

    твіни = [f"Твін {i}" for i in range(1, 10)]
    emojis = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣']
    emoji_map = dict(zip(emojis, твіни))

    дані = {твін: None for твін in твіни}
    embed = discord.Embed(title="🌀 Обери свого Твіна", color=0x0099ff)

    for твін in твіни:
        embed.add_field(name=твін, value="‎", inline=False)

    повідомлення = await ctx.send(embed=embed)

    bot.twin_messages = getattr(bot, "twin_messages", {})
    bot.twin_messages[повідомлення.id] = {
        "message": повідомлення,
        "дані": дані,
        "emoji_map": emoji_map
    }

    for emoji in emojis + ['❌', '🔁']:
        await повідомлення.add_reaction(emoji)

@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    await ctx.channel.purge(limit=amount + 1)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    message_id = reaction.message.id
    emoji = str(reaction.emoji)

    # === АКТИВНІСТЬ ===
    if message_id in reaction_data and emoji in ["👍🏻", "❓", "👎🏻"]:
        дані = reaction_data[message_id]
        учасники = дані["учасники"]

        for інше in учасники:
            if user.mention in учасники[інше]:
                учасники[інше].remove(user.mention)

        if user.mention not in учасники[emoji]:
            учасники[emoji].append(user.mention)

        try:
            await reaction.message.remove_reaction(emoji, user)
        except:
            pass

        await оновити_embed(reaction.message, дані)

    # === ТВІН ===
    if hasattr(bot, "twin_messages") and message_id in bot.twin_messages:
        twin_data = bot.twin_messages[message_id]
        emoji_map = twin_data["emoji_map"]
        дані = twin_data["дані"]

        змінились = False

        if emoji == '🔁':
            for твін in дані:
                дані[твін] = None
            змінились = True

        elif emoji == '❌':
            for твін in дані:
                if дані[твін] == user.mention:
                    дані[твін] = None
                    змінились = True

        elif emoji in emoji_map:
            обраний_твін = emoji_map[emoji]
            for твін in дані:
                if дані[твін] == user.mention:
                    дані[твін] = None
            if дані[обраний_твін] != user.mention:
                дані[обраний_твін] = user.mention
                змінились = True

        if змінились:
            новий_embed = discord.Embed(title="🌀 Обери свого Твіна", color=0x0099ff)
            for твін in дані:
                учасник = дані[твін]
                текст = f"{учасник}" if учасник else "‎"
                новий_embed.add_field(name=твін, value=текст, inline=False)
            try:
                await reaction.message.edit(embed=новий_embed)
            except:
                pass

        try:
            await asyncio.sleep(0.3)
            await reaction.message.remove_reaction(emoji, user)
        except:
            pass

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

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))