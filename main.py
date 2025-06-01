import discord
from discord.ext import commands
import asyncio
import datetime
import pytz

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

bot.activity_messages = {}
bot.twin_messages = {}

ZERO_ROLE_NAME = "Zero Tolerance"

@bot.event
async def on_ready():
    print(f"Бот запущено як {bot.user}")

@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"Очищено {amount} повідомлень.", delete_after=5)

@bot.command(name="активність")
async def активність(ctx, *, дані):
    try:
        назва, опис, дата = [частина.strip() for частина in дані.split("|")]
    except ValueError:
        await ctx.send("❌ Неправильний формат. Використай: `!активність Назва | Опис | Дата`")
        return

    try:
        дата_обʼєкт = datetime.datetime.strptime(дата, "%d.%m.%Y %H:%M")
        дата_обʼєкт = pytz.timezone("Europe/Kyiv").localize(дата_обʼєкт)
        timestamp = int(дата_обʼєкт.timestamp())
    except ValueError:
        await ctx.send("❌ Неправильний формат дати. Використай: `дд.мм.рррр гг:хх`")
        return

    згадка_ролі = discord.utils.get(ctx.guild.roles, name=ZERO_ROLE_NAME)
    згадка_текст = f"{згадка_ролі.mention} " if згадка_ролі else ""

    embed = discord.Embed(title=назва, description=опис, color=discord.Color.green())
    embed.add_field(name="Час", value=f"<t:{timestamp}:F> (<t:{timestamp}:R>)", inline=False)
    embed.set_footer(text="Оберіть реакцію:")
    message = await ctx.send(f"{згадка_текст}", embed=embed)

    for emoji in ["👍🏻", "❓", "👎🏻"]:
        await message.add_reaction(emoji)

    bot.activity_messages[message.id] = {
        "message": message,
        "реакції": {
            "👍🏻": [],
            "❓": [],
            "👎🏻": []
        }
    }

    await asyncio.sleep(10)
    await message.delete()

@bot.command(name="твін")
async def twin(ctx):
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
    дані = {f"Твін {i+1}": None for i in range(9)}

    def створити_embed():
        embed = discord.Embed(title="Вибір Твіна", color=discord.Color.blue())
        текст = "\n".join([
            f"{назва} - {дані[назва].mention if дані[назва] else ''}" for назва in дані
        ])
        embed.description = текст
        return embed

    повідомлення = await ctx.send(embed=створити_embed())

    for emoji in emojis + ["❌", "🔁"]:
        await повідомлення.add_reaction(emoji)

    bot.twin_messages[повідомлення.id] = {
        "message": повідомлення,
        "дані": дані,
        "emoji_map": {emoji: f"Твін {i+1}" for i, emoji in enumerate(emojis)},
        "ping_message_id": None
    }

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return

    channel = bot.get_channel(payload.channel_id)
    user = payload.member
    message_id = payload.message_id
    emoji = str(payload.emoji)

    # ===== Активність =====
    if message_id in bot.activity_messages:
        data = bot.activity_messages[message_id]
        for реакція in data["реакції"]:
            if user in data["реакції"][реакція]:
                data["реакції"][реакція].remove(user)
        if emoji in data["реакції"]:
            data["реакції"][emoji].append(user)

        embed = data["message"].embeds[0]
        embed.clear_fields()
        for реакція in data["реакції"]:
            учасники = ", ".join(user.mention for user in data["реакції"][реакція])
            embed.add_field(name=f"{реакція} ({len(data['реакції'][реакція])})", value=учасники or "-", inline=True)
        await data["message"].edit(embed=embed)
        await data["message"].remove_reaction(payload.emoji, user)

    # ===== Твін =====
    elif message_id in bot.twin_messages:
        twin_data = bot.twin_messages[message_id]
        дані = twin_data["дані"]
        emoji_map = twin_data["emoji_map"]
        guild = channel.guild

        if emoji in emoji_map:
            твін = emoji_map[emoji]
            for ключ in дані:
                if дані[ключ] == user:
                    дані[ключ] = None
            if дані[твін] is None:
                дані[твін] = user

        elif emoji == "❌":
            for ключ in дані:
                if дані[ключ] == user:
                    дані[ключ] = None

        elif emoji == "🔁":
            for ключ in дані:
                дані[ключ] = None

            згадка_ролі = discord.utils.get(guild.roles, name=ZERO_ROLE_NAME)
            старе_повідомлення_id = twin_data.get("ping_message_id")

            if старе_повідомлення_id:
                try:
                    старе_повідомлення = await channel.fetch_message(старе_повідомлення_id)
                    await старе_повідомлення.delete()
                except discord.NotFound:
                    pass

            if згадка_ролі:
                msg = await channel.send(f"{згадка_ролі.mention} оберіть твіна", delete_after=14400)
                twin_data["ping_message_id"] = msg.id

        embed = discord.Embed(title="Вибір Твіна", color=discord.Color.blue())
        embed.description = "\n".join([
            f"{назва} - {учасник.mention if учасник else ''}" for назва, учасник in дані.items()
        ])
        await twin_data["message"].edit(embed=embed)
        await twin_data["message"].remove_reaction(payload.emoji, user)

# 🚨 Заміни "YOUR_BOT_TOKEN" на свій реальний токен
bot.run("YOUR_BOT_TOKEN")