import os
import discord
from discord.ext import commands
from keep_alive import keep_alive
from dotenv import load_dotenv

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- Змінні для активностей ----------
activity_data = {}

# ---------- Змінні для твінів ----------
twin_data = {}
twin_names = [f"Твін {i}" for i in range(1, 10)]
twin_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']
clear_emoji = '❌'
refresh_emoji = '🔁'

# ---------- KEEP ALIVE ----------
keep_alive()

# ---------- КОМАНДА: АКТИВНІСТЬ ----------
@bot.command(name="активність")
async def activity(ctx, назва: str, *, опис: str = "Без опису"):
    embed = discord.Embed(title=назва, description=опис, color=0x00ff00)
    embed.add_field(name="👍🏻 Підтверджують", value="-", inline=True)
    embed.add_field(name="❓ Можливо", value="-", inline=True)
    embed.add_field(name="👎🏻 Відсутні", value="-", inline=True)
    embed.set_footer(text=f"Створено: <t:{int(ctx.message.created_at.timestamp())}:f>")

    message = await ctx.send(embed=embed)
    await message.add_reaction("👍🏻")
    await message.add_reaction("❓")
    await message.add_reaction("👎🏻")

    activity_data[message.id] = {
        "👍🏻": set(),
        "❓": set(),
        "👎🏻": set(),
        "author_id": ctx.author.id
    }

async def update_activity_embed(message):
    data = activity_data.get(message.id)
    if not data:
        return

    embed = message.embeds[0]
    for i, emoji in enumerate(["👍🏻", "❓", "👎🏻"]):
        names = " - " + "\n - ".join(user.mention for user in data[emoji]) if data[emoji] else "-"
        embed.set_field_at(i, name=embed.fields[i].name, value=names, inline=True)

    await message.edit(embed=embed)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    message_id = reaction.message.id

    # === АКТИВНІСТЬ ===
    if message_id in activity_data:
        for emoji in ["👍🏻", "❓", "👎🏻"]:
            if emoji != str(reaction.emoji):
                activity_data[message_id][emoji].discard(user)
        if str(reaction.emoji) in activity_data[message_id]:
            activity_data[message_id][str(reaction.emoji)].add(user)
            await update_activity_embed(reaction.message)
            await reaction.message.remove_reaction(reaction.emoji, user)

    # === ТВІНИ ===
    if message_id in twin_data:
        if str(reaction.emoji) == refresh_emoji:
            twin_data[message_id] = {}
        elif str(reaction.emoji) == clear_emoji:
            for twin, assigned in twin_data[message_id].items():
                if assigned == user:
                    twin_data[message_id][twin] = None
        elif str(reaction.emoji) in twin_emojis:
            twin_index = twin_emojis.index(str(reaction.emoji))
            twin = twin_names[twin_index]

            # Зняти користувача з інших твинів
            for key in twin_data[message_id]:
                if twin_data[message_id][key] == user:
                    twin_data[message_id][key] = None

            # Якщо твін вже зайнятий іншим — не перезаписуємо
            if twin_data[message_id].get(twin) is None:
                twin_data[message_id][twin] = user

        await оновити_twin_embed(reaction.message, twin_data[message_id])
        await reaction.message.remove_reaction(reaction.emoji, user)

# ---------- КОМАНДА: ТВІНИ ----------
@bot.command(name="твіни")
async def twin_command(ctx):
    embed = discord.Embed(title="Вибір Твіна", color=0x3498db)
    message = await ctx.send(embed=embed)

    twin_data[message.id] = {twin: None for twin in twin_names}

    for emoji in twin_emojis + [clear_emoji, refresh_emoji]:
        await message.add_reaction(emoji)

    await оновити_twin_embed(message, twin_data[message.id])

async def оновити_twin_embed(message, data):
    embed = discord.Embed(title="Вибір Твіна", color=0x3498db)
    for twin in twin_names:
        user = data.get(twin)
        display = f"- {user.mention}" if user else "-"
        embed.add_field(name=twin, value=display, inline=True)
    await message.edit(embed=embed)

# ---------- КОМАНДА: CLEAR ----------
@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 Видалено {amount} повідомлень.", delete_after=3)

# ---------- ЗАПУСК ----------
bot.run(os.getenv("DISCORD_TOKEN"))