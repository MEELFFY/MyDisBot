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

ZERO_ROLE_NAME = "Zero Tolerance"

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
        else:
            опис = частини[1].strip()
            дата_час = частини[2].strip()
            таймзона = частини[3].strip() if len(частини) >= 4 else "Europe/Kyiv"

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
            embed.add_field(name=f"{emoji} (0)", value="Ніхто", inline=True)

        згадка_ролі = discord.utils.get(ctx.guild.roles, name=ZERO_ROLE_NAME)
        повідомлення = await ctx.send(f"{згадка_ролі.mention if згадка_ролі else ''}", embed=embed)

        reaction_data[повідомлення.id] = {
            "message": повідомлення,
            "учасники": учасники
        }

        for emoji in учасники:
            await повідомлення.add_reaction(emoji)

        await asyncio.sleep(залишилось.total_seconds())
        try:
            await повідомлення.delete()
        except:
            pass

    except Exception as e:
        await ctx.send(f"⚠️ Помилка: {e}", delete_after=8)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
    channel = guild.get_channel(payload.channel_id)
    user = guild.get_member(payload.user_id)
    message = await channel.fetch_message(payload.message_id)
    emoji = str(payload.emoji)

    # Активність
    if message.id in reaction_data and emoji in ["👍🏻", "❓", "👎🏻"]:
        дані = reaction_data[message.id]
        учасники = дані["учасники"]

        for інше_емоджі in учасники:
            if user.mention in учасники[інше_емоджі]:
                учасники[інше_емоджі].remove(user.mention)

        учасники[emoji].append(user.mention)

        try:
            await message.remove_reaction(emoji, user)
        except:
            pass

        await оновити_embed(message, дані)

    # Твін
    elif hasattr(bot, "twin_messages") and message.id in bot.twin_messages:
        twin_data = bot.twin_messages[message.id]
        emoji_map = twin_data["emoji_map"]
        дані = twin_data["дані"]

        if emoji == '🔁':
            for ключ in дані:
                дані[ключ] = []

            згадка_ролі = discord.utils.get(guild.roles, name=ZERO_ROLE_NAME)
            if згадка_ролі:
                info = await channel.send(f"{згадка_ролі.mention} оберіть твіна", delete_after=14400)

        elif emoji == '❌':
            for ключ in дані:
                if user.mention in дані[ключ]:
                    дані[ключ].remove(user.mention)
        elif emoji in emoji_map:
            for ключ in дані:
                if user.mention in дані[ключ]:
                    дані[ключ].remove(user.mention)
            твін = emoji_map[emoji]
            дані[твін].append(user.mention)

        новий_embed = discord.Embed(title="🌀 Обери свого Твіна", color=0x0099ff)
        опис = ""
        for твін in дані:
            учасники = " – " + ", ".join(дані[твін]) if дані[твін] else " –"
            опис += f"{твін}{учасники}\n"
        новий_embed.description = опис
        await message.edit(embed=новий_embed)

        try:
            await message.remove_reaction(payload.emoji, user)
        except:
            pass

async def оновити_embed(повідомлення, дані):
    старий = повідомлення.embeds[0]
    новий = discord.Embed(
        title=старий.title,
        description=старий.description,
        color=старий.color
    )

    for emoji in ["👍🏻", "❓", "👎🏻"]:
        список = "\n".join(дані["учасники"][emoji]) if дані["учасники"][emoji] else "Ніхто"
        кількість = len(дані["учасники"][emoji])
        новий.add_field(name=f"{emoji} ({кількість})", value=список, inline=True)

    await повідомлення.edit(embed=новий)

@bot.command(name="твін")
async def твін(ctx):
    await ctx.message.delete()

    твіни = [f"Твін {i}" for i in range(1, 10)]
    emojis = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣']
    emoji_map = dict(zip(emojis, твіни))

    дані = {твін: [] for твін in твіни}

    embed = discord.Embed(title="🌀 Обери свого Твіна", color=0x0099ff)
    опис = ""
    for твін in твіни:
        учасники = " – " + ", ".join(дані[твін]) if дані[твін] else " –"
        опис += f"{твін}{учасники}\n"
    embed.description = опис.strip()

    повідомлення = await ctx.send(embed=embed)

    bot.twin_messages = getattr(bot, "twin_messages", {})
    bot.twin_messages[повідомлення.id] = {
        "message": повідомлення,
        "дані": дані,
        "emoji_map": emoji_map
    }

    for emoji in emojis + ['❌', '🔁']:
        await повідомлення.add_reaction(emoji)

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))