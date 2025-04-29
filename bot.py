import os
import re
import trace
import cv2

import time
import emoji
import shutil
import discord

import asyncio
import requests
import threading
import traceback
import subprocess
import unicodedata

import numpy as np

from datetime import datetime
from huggingface_hub import HfApi, HfFolder, Repository
from discord_webhook import DiscordWebhook, DiscordEmbed
from apscheduler.schedulers.asyncio import AsyncIOScheduler

WEBH_URL = "Webhook URL" # Webhook For Image Scrapper Logs
DC_TOKEN = "Discord Bot Token" # Token For Discord Bot To Collect Images - https://discord.com/developers/applications
AUTO_UPLOAD_CHANNEL_ID = 00000000000 # Discord Uploader Log Channel

HF_TOKEN = "Hugging Face Token" # Token For Hugging Face Uplaods - https://huggingface.co/settings/tokens
HfFolder.save_token(HF_TOKEN)

upload_started_time = time.time()
scheduler = AsyncIOScheduler()

uploading = False
batch_size = 1000
folder_per_batch = 50
images_per_class = 90
total_pokemon_count = 0
upload_lock = threading.Lock()


def discord_log(pokemon, count, total, url):
    webhook = DiscordWebhook(
        url=WEBH_URL,
    )
    embed = DiscordEmbed(
        title="Pokemon Image Collector",
        description=f"Pokemon: **{pokemon}**\nCount: **{count}/{images_per_class}**\n\nTotal Collected: **{total}**",
        color=0x7289DA,
    )
    if url:
        embed.set_image(url=url)

    webhook.add_embed(embed)
    webhook.execute()


def remove_diacritics(text):
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


def remove_emoji(text):
    text = emoji.demojize(text)

    text = re.sub(r":female_sign:", "F", text)
    text = re.sub(r":female:", "F", text)

    text = re.sub(r":male_sign:", "M", text)
    text = re.sub(r":male:", "M", text)

    return text


def extract_pokemon_name(text):
    pattern = r"Level \d+ (.+?):(:?[a-z]+:)"
    match = re.search(pattern, text)

    return match.group(1).strip() if match else None


def save(image_url, pokemon_name):
    global total_pokemon_count

    pokemon_name = pokemon_name.replace("<", "").lower()

    try:
        response = requests.get(image_url, stream=True, timeout=10)
        response.raise_for_status()
        img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_UNCHANGED)
    except Exception as e:
        print(f"[ERROR] Failed To Download Or Decode Image : {e}")
        return

    folder = os.path.join("pokemons", pokemon_name)
    os.makedirs(folder, exist_ok=True)

    current_count = len([f for f in os.listdir(folder) if f.endswith(".jpg")])

    if current_count < images_per_class:
        filename = os.path.join(folder, f"{int(time.time())}.jpg")
        try:
            cv2.imwrite(filename, image)
            total_pokemon_count += 1

            print(
                f"[+] Saved {pokemon_name} Image ({current_count+1}/{images_per_class})"
            )
            discord_log(
                pokemon_name,
                count=current_count + 1,
                total=total_pokemon_count,
                url=image_url,
            )
        except Exception as e:
            print(f"[ERROR] Failed To Save Image : {e}")


def upload_pokemons_to_huggingface():
    global uploading

    if uploading:
        print("[!] Already Uploading Pokémon Images")
        return

    uploading = True
    upload_started_time = time.time()

    try:
        api = HfApi(token=HF_TOKEN)
        all_folders = sorted(
            [
                f
                for f in os.listdir("pokemons")
                if os.path.isdir(os.path.join("pokemons", f))
            ]
        )
        total = len(all_folders)
        print(f"[i] Found {total} Pokémon Folders TO Upload")

        for i in range(0, total, folder_per_batch):
            batch = all_folders[i : i + folder_per_batch]
            temp_dir = os.path.join("pokemons", "__temp_upload__")
            os.makedirs(temp_dir, exist_ok=True)

            for folder in batch:
                src = os.path.join("pokemons", folder)
                dst = os.path.join(temp_dir, folder)
                shutil.copytree(src, dst)

            commit_msg = f"Upload batch {i}-{i+len(batch)} @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            try:
                api.upload_folder(
                    folder_path=temp_dir,
                    repo_id="SpreadSheets600/Poketwo-Spawn-Images",
                    repo_type="dataset",
                    commit_message=commit_msg,
                )
                print(f"[+] Uploaded Pokémon Batch : {batch}")
            except Exception as e:
                print(f"[❌] Failed To Upload Batch {batch} : {e}")
            finally:
                shutil.rmtree(temp_dir)

            time.sleep(2)

        print("[✅] All Folders Uploaded Successfully!")

    except Exception as e:
        print(f"[❌] Upload Failed : {e}")
        traceback.print_exc()

    finally:
        if time.time() - upload_started_time > 60 * 15:
            print("[!] Upload Timeout Triggered.")
        uploading = False


class PokemonCollector(discord.Bot):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.scheduler = AsyncIOScheduler()
        self.scheduler_started = False

        @self.command(
            name="upload", description="Upload Pokémon Images To Hugging Face"
        )
        async def upload(ctx):
            global uploading

            if uploading:
                await ctx.respond("⚠️ Already Uploading Pokémon Images. Please Wait...")
                return

            await ctx.respond("📤 Uploading Pokémon Images To Hugging Face...")

            def threaded_upload():
                upload_pokemons_to_huggingface()

                coro = (
                    ctx.send("✅ Upload Complete!")
                    if not uploading
                    else ctx.send("❌ Upload Failed!")
                )
                asyncio.run_coroutine_threadsafe(coro, self.loop)

            threading.Thread(target=threaded_upload).start()

    async def on_ready(self):
        print(f"[+] Logged In As {self.user} ({self.user.id})")

        if not self.scheduler_started:
            self.scheduler_started = True

            self.scheduler.add_job(self.daily_upload, "cron", hour=0, minute=0)
            self.scheduler.start()

            print("[+] Scheduler Started For Daily Uploads.")

    async def daily_upload(self):
        channel = self.get_channel(AUTO_UPLOAD_CHANNEL_ID)
        if not channel:
            print("[!] Channel Not Found For Daily Upload Log!")
            return

        if uploading:
            await channel.send("⚠️ Daily Upload Skipped : Already In Progress.")
            return

        await channel.send("📤 Daily Upload Started ...")

        def threaded_upload():
            success = upload_pokemons_to_huggingface()
            coro = channel.send(
                "✅ Daily Upload Complete!" if success else "❌ Daily Upload Failed!"
            )
            asyncio.run_coroutine_threadsafe(coro, self.loop)

        threading.Thread(target=threaded_upload).start()

    async def on_message(self, message):
        global uploading

        if uploading:
            return

        try:
            if not message.guild or message.author.id != 716390085896962058:
                return

            if (
                message.content.startswith("Congratulations")
                and "You caught a Level" in message.content
            ):
                pokemon_name = extract_pokemon_name(message.content)
                if not pokemon_name:
                    print("[!] Could Not Extract Pokemon Name")
                    return

                pokemon_name = remove_emoji(remove_diacritics(pokemon_name))

                async for msg in message.channel.history(limit=30, oldest_first=False):
                    if msg.embeds:
                        embed = msg.embeds[0]
                        if "wild pokémon has appeared!" in embed.title.lower():
                            if embed.image and embed.image.url:
                                threading.Thread(
                                    target=save, args=(embed.image.url, pokemon_name)
                                ).start()
                                return

                print("[!] Spawn Embed Not Found")

        except Exception as e:
            print(f"[!] Error : {e}")
            return


client = PokemonCollector()
client.run(DC_TOKEN)
