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
            await ctx.send("❌ Формат:\nЗ описом: !активність Назва | Опис | Дата`\nБез опису: !активність Назва | Дата`", delete_after=10)
            return

        назва = частини[0].strip()
        опис = частини[1].strip() if len(частини) >= 3 else ""
        дата_час = частини[-2].strip()
        таймзона = частини[-1].strip() if len(частини) >= 4 else "Europe/Kyiv"

        dt = datetime.datetime.strptime(дата_час, "%Y-%m-%d %H:%M")
        локальна_таймзона = pytz.timezone(таймзона)
        локальний_час = локальна_таймзона.localize(dt)
        час_utc = локальний_час.astimezone(pytz.utc)

        зараз = datetime.datetime.now(pytz.utc)
        залишилось = час_utc - зараз

        if залишилось.total_seconds() <= 0:
            await ctx.send("❌ Вказана дата/час уже минули.", delete_after=5)
            return

        учасники = { "👍🏻": [], "❓": [], "👎🏻": [] }
        timestamp = int(час_utc.timestamp())

        embed = discord.Embed(title=f"📢 {назва}", color=0x00ff00)
        embed.description = f"{опис}\n\n📅 <t:{timestamp}:F> (<t:{timestamp}:R>)" if опис else f"📅 <t:{timestamp}:F> (<t:{timestamp}:R>)"
        for emoji in учасники:
            embed.add_field(name=f"{emoji} (0)", value="-", inline=True)

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

    # --- Активність ---
    if message_id in reaction_data and emoji in reaction_data[message_id]["учасники"]:
        дані = reaction_data[message_id]
        учасники = дані["учасники"]

        # Забрати користувача з інших емоцій
        for інше_емоджі in учасники:
            if user.mention in учасники[інше_емоджі]:
                учасники[інше_емоджі].remove(user.mention)

        # Додати до нової емоції
        if user.mention not in учасники[emoji]:
            учасники[emoji].append(user.mention)

        # Зняти реакцію
        try:
            await reaction.message.remove_reaction(emoji, user)
        except:
            pass

        await оновити_embed(reaction.message, дані)

    # --- Твіни ---
    elif message_id in twin_data:
        if emoji == "🔁":
            twin_data[message_id] = {f"Твін {i}": None for i in range(1, 10)}
        elif emoji == "❌":
            for твін in twin_data[message_id]:
                if twin_data[message_id][твін] == user.mention:
                    twin_data[message_id][твін] = None
        elif emoji in ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]:
            твін_номер = int("123456789".index(emoji) + 1)
            вибраний = f"Твін {твін_номер}"

            # Забрати користувача з усіх твинів
            for твін in twin_data[message_id]:
                if twin_data[message_id][твін] == user.mention:
                    twin_data[message_id][твін] = None

            # Якщо твіна не зайнято, додати користувача
            if twin_data[message_id][вибраний] is None:
                twin_data[message_id][вибраний] = user.mention
            
            await оновити_twin_embed(reaction.message, twin_data[message_id])

async def оновити_embed(повідомлення, дані):
    старий = повідомлення.embeds[0]
    новий = discord.Embed(title=старий.title, description=старий.description, color=старий.color)

    for emoji in ["👍🏻", "❓", "👎🏻"]:
        список = " - " + " | ".join(дані["учасники"][emoji]) if дані["учасники"][emoji] else "-"
        новий.add_field(name=f"{emoji} ({len(дані['учасники'][emoji])})", value=список, inline=True)

    await повідомлення.edit(embed=новий)

@bot.command(name="твіни")
async def твіни(ctx):
    список = {f"Твін {i}": None for i in range(1, 10)}
    embed = discord.Embed(title="🎭 Вибір Твінів", color=0x3498db)

    for твін in список:
        embed.add_field(name=твін, value="-", inline=True)

    повідомлення = await ctx.send(embed=embed)
    twin_data[повідомлення.id] = список

    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "❌", "🔁"]
    for emoji in emojis:
        await повідомлення.add_reaction(emoji)

async def оновити_twin_embed(повідомлення, дані):
    embed = discord.Embed(title="🎭 Вибір Твінів", color=0x3498db)

    for твін in дані:
        значення = f"- {дані[твін]}" if дані[твін] else "-"
        embed.add_field(name=твін, value=значення, inline=True)

    await повідомлення.edit(embed=embed)

keep_alive()
bot.run(os.getenv("TOKEN"))
