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
            await ctx.send("❌ Формат:\n`!активність Назва | Опис | Дата`\nабо\n`!активність Назва | Дата`", delete_after=10)
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
        embed.description = f"{опис}\n\n📅 <t:{timestamp}:F> (<t:{timestamp}:R>)" if опис else f"📅 <t:{timestamp}:F> (<t:{timestamp}:R>)"

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
        await ctx.send(f"⚠️ Помилка: {e}", delete_after=10)

async def оновити_активність_embed(повідомлення, дані):
    старий = повідомлення.embeds[0]
    новий = discord.Embed(title=старий.title, description=старий.description, color=старий.color)

    учасники = дані["учасники"]
    for emoji in ["👍🏻", "❓", "👎🏻"]:
        список = "\n".join(учасники[emoji]) if учасники[emoji] else "Ніхто"
        новий.add_field(name=f"{emoji} ({len(учасники[emoji])})", value=список, inline=True)

    await повідомлення.edit(embed=новий)

@bot.command(name="твін")
async def твін(ctx):
    await ctx.message.delete()

    твіни = [f"Твін {i}" for i in range(1, 10)]
    emojis = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣']
    emoji_map = dict(zip(emojis, твіни))

    дані = {твін: "" for твін in твіни}

    embed = discord.Embed(title="🌀 Обери свого Твіна", color=0x0099ff)
    текст = "\n".join([f"**{твін}** - {дані[твін]}" for твін in твіни])
    embed.description = текст

    повідомлення = await ctx.send(embed=embed)

    twin_data[повідомлення.id] = {
        "message": повідомлення,
        "дані": дані,
        "emoji_map": emoji_map
    }

    for emoji in emojis + ['❌', '🔁']:
        await повідомлення.add_reaction(emoji)

@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    await ctx.message.delete()
    deleted = await ctx.channel.purge(limit=amount)
    await ctx.send(f"🧹 Видалено {len(deleted)} повідомлень", delete_after=5)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    message_id = reaction.message.id
    emoji = str(reaction.emoji)

    # Активність
    if message_id in reaction_data and emoji in ["👍🏻", "❓", "👎🏻"]:
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

        await оновити_активність_embed(reaction.message, дані)

    # Твіни
    elif message_id in twin_data:
        twin = twin_data[message_id]
        if emoji == '🔁':
            for ключ in twin["дані"]:
                twin["дані"][ключ] = ""
        elif emoji == '❌':
            for ключ in twin["дані"]:
                if user.mention in twin["дані"][ключ]:
                    twin["дані"][ключ] = ""
        elif emoji in twin["emoji_map"]:
            for ключ in twin["дані"]:
                if user.mention in twin["дані"][ключ]:
                    twin["дані"][ключ] = ""

            твін = twin["emoji_map"][emoji]
            twin["дані"][твін] = user.mention

        текст = "\n".join([f"**{твін}** - {twin['дані'][твін]}" for твін in twin["дані"]])
        новий_embed = discord.Embed(title="🌀 Обери свого Твіна", description=текст, color=0x0099ff)

        await reaction.message.edit(embed=новий_embed)

        try:
            await reaction.message.remove_reaction(emoji, user)
        except:
            pass

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))