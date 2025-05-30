import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
import threading
from utils import check_ban, get_player_info

app = Flask(__name__)

load_dotenv()
APPLICATION_ID = os.getenv("APPLICATION_ID")
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DEFAULT_LANG = "en"
user_languages = {}

nomBot = "None"

@app.route('/')
def home():
    global nomBot
    return f"Bot {nomBot} is working"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_flask).start()

@bot.event
async def on_ready():
    global nomBot
    nomBot = f"{bot.user}"
    print(f"Le bot est connecté en tant que {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.command(name="guilds")
async def show_guilds(ctx):
    guild_names = [f"{i+1}. {guild.name}" for i, guild in enumerate(bot.guilds)]
    guild_list = "\n".join(guild_names)
    await ctx.send(f"Le bot est dans les guilds suivantes :\n{guild_list}")

@bot.command(name="lang")
async def change_language(ctx, lang_code: str):
    lang_code = lang_code.lower()
    if lang_code not in ["en", "fr"]:
        await ctx.send("❌ Invalid language. Available: `en`, `fr`")
        return

    user_languages[ctx.author.id] = lang_code
    message = "✅ Language set to English." if lang_code == 'en' else "✅ Langue définie sur le français."
    await ctx.send(f"{ctx.author.mention} {message}")

@bot.command(name="ID")
async def check_ban_command(ctx):
    content = ctx.message.content
    user_id = content[3:].strip()
    lang = user_languages.get(ctx.author.id, "en")

    print(f"Commande fait par {ctx.author} (lang={lang})")

    if not user_id.isdigit():
        message = {
            "en": f"{ctx.author.mention} ❌ **Invalid UID!**\n➡️ Please use: `!ID 123456789`",
            "fr": f"{ctx.author.mention} ❌ **UID invalide !**\n➡️ Veuillez fournir un UID valide sous la forme : `!ID 123456789`"
        }
        await ctx.send(message[lang])
        return

    async with ctx.typing():
        try:
            ban_status = await check_ban(user_id)
        except Exception as e:
            await ctx.send(f"{ctx.author.mention} ⚠️ Error:\n```{str(e)}```")
            return

        if ban_status is None:
            message = {
                "en": f"{ctx.author.mention} ❌ **Could not get information. Please try again later.**",
                "fr": f"{ctx.author.mention} ❌ **Impossible d'obtenir les informations.**\nVeuillez réessayer plus tard."
            }
            await ctx.send(message[lang])
            return

        is_banned = int(ban_status.get("is_banned", 0))
        period = ban_status.get("period", "N/A")
        nickname = ban_status.get("nickname", "NA")
        region = ban_status.get("region", "N/A")
        id_str = f"`{user_id}`"

        if isinstance(period, int):
            period_str = f"more than {period} months" if lang == "en" else f"plus de {period} mois"
        else:
            period_str = "unavailable" if lang == "en" else "indisponible"

        embed = discord.Embed(
            color=0xFF0000 if is_banned else 0x00FF00,
            timestamp=ctx.message.created_at
        )

        if is_banned:
            embed.title = "**▌ Banned Account 🛑 **" if lang == "en" else "**▌ Compte banni 🛑 **"
            embed.description = (
                f"**• {'Reason' if lang == 'en' else 'Raison'} :** "
                f"{'This account was confirmed for using cheats.' if lang == 'en' else 'Ce compte a été confirmé comme utilisant des hacks.'}\n"
                f"**• {'Suspension duration' if lang == 'en' else 'Durée de la suspension'} :** {period_str}\n"
                f"**• {'Nickname' if lang == 'en' else 'Pseudo'} :** `{nickname}`\n"
                f"**• {'Player ID' if lang == 'en' else 'ID du joueur'} :** `{id_str}`\n"
                f"**• {'Region' if lang == 'en' else 'Région'} :** `{region}`"
            )
            # embed.set_image(url="https://i.ibb.co/wFxTy8TZ/banned.gif")
            file = discord.File("assets/banned.gif", filename="banned.gif")
            embed.set_image(url="attachment://banned.gif")
        else:
            embed.title = "**▌ Clean Account ✅ **" if lang == "en" else "**▌ Compte non banni ✅ **"
            embed.description = (
                f"**• {'Status' if lang == 'en' else 'Statut'} :** "
                f"{'No sufficient evidence of cheat usage on this account.' if lang == 'en' else 'Aucune preuve suffisante pour confirmer l’utilisation de hacks sur ce compte.'}\n"
                f"**• {'Nickname' if lang == 'en' else 'Pseudo'} :** `{nickname}`\n"
                f"**• {'Player ID' if lang == 'en' else 'ID du joueur'} :** `{id_str}`\n"
                f"**• {'Region' if lang == 'en' else 'Région'} :** `{region}`"
            )
            # embed.set_image(url="https://i.ibb.co/Kx1RYVKZ/notbanned.gif")
            file = discord.File("assets/notbanned.gif", filename="notbanned.gif")
            embed.set_image(url="attachment://notbanned.gif")

        embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.set_footer(text="📌  Garena Free Fire")
        await ctx.send(f"{ctx.author.mention}", embed=embed ,file=file)

@bot.tree.command(name="info", description="Get Free Fire player information")
async def player_info_slash_command(interaction: discord.Interaction, region: str, uid: str):
    lang = user_languages.get(interaction.user.id, "en")
    
    print(f"Info slash command by {interaction.user} (lang={lang}, uid={uid}, region={region})")

    if not uid.isdigit():
        message = {
            "en": f"❌ **Invalid UID!**\n➡️ Please use: `/info ind 123456789`",
            "fr": f"❌ **UID invalide !**\n➡️ Veuillez utiliser : `/info ind 123456789`"
        }
        await interaction.response.send_message(message[lang], ephemeral=True)
        return

    await interaction.response.defer()

    try:
        player_data = await get_player_info(uid, region.upper())
    except Exception as e:
        await interaction.followup.send(f"⚠️ Error:\n```{str(e)}```", ephemeral=True)
        return

    if player_data is None:
        message = {
            "en": f"❌ **Could not get player information. Please try again later.**",
            "fr": f"❌ **Impossible d'obtenir les informations du joueur.**\nVeuillez réessayer plus tard."
        }
        await interaction.followup.send(message[lang], ephemeral=True)
        return

    # Extract player information
    account_info = player_data.get("AccountInfo", {})
    guild_info = player_data.get("GuildInfo", {})
    social_info = player_data.get("socialinfo", {})
    credit_info = player_data.get("creditScoreInfo", {})

    nickname = account_info.get("AccountName", "N/A")
    level = account_info.get("AccountLevel", "N/A")
    likes = account_info.get("AccountLikes", "N/A")
    br_rank = account_info.get("BrMaxRank", "N/A")
    cs_rank = account_info.get("CsMaxRank", "N/A")
    region_code = account_info.get("AccountRegion", "N/A")
    guild_name = guild_info.get("GuildName", "No Guild")
    signature = social_info.get("AccountSignature", "No signature")
    credit_score = credit_info.get("creditScore", "N/A")

    embed = discord.Embed(
        color=0x00FF9F,
        timestamp=interaction.created_at
    )

    if lang == "en":
        embed.title = f"**🎮 Player Info: {nickname}**"
        embed.description = (
            f"**• Player ID:** `{uid}`\n"
            f"**• Nickname:** `{nickname}`\n"
            f"**• Level:** `{level}`\n"
            f"**• Region:** `{region_code}`\n"
            f"**• Likes:** `{likes:,}` 👍\n"
            f"**• BR Max Rank:** `{br_rank}`\n"
            f"**• CS Max Rank:** `{cs_rank}`\n"
            f"**• Guild:** `{guild_name}`\n"
            f"**• Credit Score:** `{credit_score}`\n"
            f"**• Signature:** `{signature[:100]}{'...' if len(signature) > 100 else ''}`"
        )
    else:
        embed.title = f"**🎮 Infos du joueur : {nickname}**"
        embed.description = (
            f"**• ID du joueur :** `{uid}`\n"
            f"**• Pseudo :** `{nickname}`\n"
            f"**• Niveau :** `{level}`\n"
            f"**• Région :** `{region_code}`\n"
            f"**• J'aime :** `{likes:,}` 👍\n"
            f"**• Rang BR Max :** `{br_rank}`\n"
            f"**• Rang CS Max :** `{cs_rank}`\n"
            f"**• Guilde :** `{guild_name}`\n"
            f"**• Score de crédit :** `{credit_score}`\n"
            f"**• Signature :** `{signature[:100]}{'...' if len(signature) > 100 else ''}`"
        )

    embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
    embed.set_footer(text="📌  Garena Free Fire")
    await interaction.followup.send(f"{interaction.user.mention}", embed=embed)

bot.run(TOKEN)
