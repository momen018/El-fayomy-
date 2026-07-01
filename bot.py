import os
import discord
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

# =======================
# CONFIGURATION
# =======================

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1488316552263630953

CITY = "Cairo"
COUNTRY = "Egypt"
METHOD = 5  # Egyptian General Authority of Survey

# =======================

intents = discord.Intents.default()
client = discord.Client(intents=intents)

scheduler = AsyncIOScheduler()


async def send_message(message):
    channel = client.get_channel(CHANNEL_ID)

    if channel:
        await channel.send(
            message,
            allowed_mentions=discord.AllowedMentions(everyone=True)
        )


async def fajr():
    await send_message("@everyone\n\nالصلاة خير من النوم يا بطل ❤️")


async def prayer():
    await send_message(
        "@everyone\n\n"
        "اذهب إلى الصلاة 🕌\n"
        "(ما بارك الله في عملٍ يلهي عن الصلاة)"
    )


def clear_jobs():
    for job in scheduler.get_jobs():
        if job.id != "refresh":
            scheduler.remove_job(job.id)


def schedule_today():
    clear_jobs()

    today = datetime.now().strftime("%d-%m-%Y")

    url = (
        f"https://api.aladhan.com/v1/timingsByCity/"
        f"{today}"
        f"?city={CITY}"
        f"&country={COUNTRY}"
        f"&method={METHOD}"
    )

    response = requests.get(url).json()
    timings = response["data"]["timings"]

    prayers = {
        "Fajr": fajr,
        "Dhuhr": prayer,
        "Asr": prayer,
        "Maghrib": prayer,
        "Isha": prayer,
    }

    for prayer_name, func in prayers.items():
        hour, minute = map(int, timings[prayer_name].split(":"))

        scheduler.add_job(
            lambda f=func: client.loop.create_task(f()),
            "cron",
            hour=hour,
            minute=minute,
            id=prayer_name,
            replace_existing=True
        )

    print("Today's prayer times loaded:")
    print(timings)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    schedule_today()

    if not scheduler.get_job("refresh"):
        scheduler.add_job(
            schedule_today,
            "cron",
            hour=0,
            minute=1,
            id="refresh"
        )

    if not scheduler.running:
        scheduler.start()


if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is not set.")

client.run(TOKEN)