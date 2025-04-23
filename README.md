# Pokétwo Spawn Image Collector 🤖🎒

A Discord bot built to collect, store, and upload Pokétwo spawn images to [Hugging Face Datasets](https://huggingface.co/datasets). Automatically detects catches, saves high-quality images, and uploads them daily — all with a single command or scheduled job. Built for collectors, AI training, or dataset nerds.

### [Link To My Implemented Dataset](https://huggingface.co/datasets/SpreadSheets600/Poketwo-Spawn-Images)

## ✨ Features

- 📤 **Manual and scheduled uploads** to Hugging Face every day at **12:00 AM**
- 🗂️ **Organizes images** by Pokémon name (90 images per class limit)
- 📸 **Auto-detects Pokétwo catches** from your Discord server
- 🕹️ **Slash command (`/upload`)** to trigger uploads any time
- 📢 **Auto-log upload status** in a specified Discord channel
- 🔒 Safe filename handling, emoji and accent cleanup
- 🔄 **Commit messages with timestamps**

---

## 📦 Requirements

- Python 3.8+
- Discord Bot Token
- Hugging Face Token
- Hugging Face Dataset Repo
- A Discord Webhook URL for logging (optional)
- [Pokétwo bot](https://top.gg/bot/716390085896962058) running in your server

---

## 🛠 Setup

1. **Clone the Repo**
   ```bash
   git clone https://github.com/yourusername/poketwo-image-collector.git
   cd poketwo-image-collector
   ```

2. **Install Requirements**
   ```bash
   pip install -r requirements.txt
   ```

3. **Add Environment Variables** (or replace directly in the script)
   ```
   DC_TOKEN=your_discord_token
   HF_TOKEN=your_huggingface_token
   WEBH_URL=https://discord.com/api/webhooks/...
   AUTO_UPLOAD_CHANNEL_ID=1234567890
   ```

4. **Run the Bot**
   ```bash
   python bot.py
   ```

---

## 🧪 Commands

| Command   | Description                         |
|-----------|-------------------------------------|
| `/upload` | Manually upload collected images    |

---

## 📅 Auto Upload

Uploads all collected images to Hugging Face every day at **12:00 AM server time**, logs the status to the configured Discord channel.

---

## 🧼 Cleaning & Normalization

- Removes emojis and diacritics from Pokémon names
- Automatically organizes folders by lowercase names
- Skips saving if the image already exists

---

## 💾 Dataset Storage

- Stored locally in `pokemons/` folder
- Uploaded to: `https://huggingface.co/datasets/your_username/your_repo`

---
