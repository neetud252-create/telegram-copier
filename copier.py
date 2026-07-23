import asyncio
import os
import re
import logging
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================
# Get credentials from environment variables
API_ID = int(os.environ.get('TELEGRAM_API_ID', 0))
API_HASH = os.environ.get('TELEGRAM_API_HASH', '')
STRING_SESSION = os.environ.get('TELEGRAM_STRING_SESSION', '')

# Source and Destination
SOURCE_CHANNEL = os.environ.get('SOURCE_CHANNEL', '')
DESTINATION_CHANNEL = os.environ.get('DESTINATION_CHANNEL', '')

# ==================== FILTER RULES ====================
# Get filters from environment variables
include_keywords_env = os.environ.get('INCLUDE_KEYWORDS', '')
EXCLUDE_KEYWORDS_ENV = os.environ.get('EXCLUDE_KEYWORDS', '')

INCLUDE_KEYWORDS = [kw.strip() for kw in include_keywords_env.split(',') if kw.strip()]
EXCLUDE_KEYWORDS = [kw.strip() for kw in EXCLUDE_KEYWORDS_ENV.split(',') if kw.strip()]

# Replacements
replacements_env = os.environ.get('REPLACEMENTS', '')
REPLACEMENTS = {}
if replacements_env:
    for pair in replacements_env.split(','):
        if ':' in pair:
            old, new = pair.split(':', 1)
            REPLACEMENTS[old.strip()] = new.strip()

# ==================== SCRIPT LOGIC ====================
class TelegramCopier:
    def __init__(self):
        self.client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
        self.source_id = None
        self.dest_id = None
        self.is_running = True
        
    async def start(self):
        """Start the copier"""
        logger.info("🚀 Starting Telegram Copier...")
        logger.info(f"📡 Source: {SOURCE_CHANNEL}")
        logger.info(f"📤 Destination: {DESTINATION_CHANNEL}")
        
        if not STRING_SESSION:
            logger.error("❌ No STRING_SESSION found! Please set TELEGRAM_STRING_SESSION")
            return
            
        try:
            await self.client.start()
            logger.info("✅ Connected to Telegram!")
            
            # Get channel IDs
            try:
                if SOURCE_CHANNEL.startswith('@'):
                    entity = await self.client.get_entity(SOURCE_CHANNEL)
                    self.source_id = entity.id
                    logger.info(f"✅ Source: {SOURCE_CHANNEL} (ID: {self.source_id})")
                else:
                    self.source_id = int(SOURCE_CHANNEL)
                    logger.info(f"✅ Source ID: {self.source_id}")
                
                if DESTINATION_CHANNEL.startswith('@'):
                    entity = await self.client.get_entity(DESTINATION_CHANNEL)
                    self.dest_id = entity.id
                    logger.info(f"✅ Destination: {DESTINATION_CHANNEL} (ID: {self.dest_id})")
                else:
                    self.dest_id = int(DESTINATION_CHANNEL)
                    logger.info(f"✅ Destination ID: {self.dest_id}")
                    
            except Exception as e:
                logger.error(f"❌ Error getting channel IDs: {e}")
                return
            
            # Test message
            try:
                await self.client.send_message(
                    self.dest_id, 
                    f"🤖 Copier started!\n\n"
                    f"📡 Monitoring: {SOURCE_CHANNEL}\n"
                    f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"📊 Filters active: {len(INCLUDE_KEYWORDS)} include, {len(EXCLUDE_KEYWORDS)} exclude"
                )
                logger.info("✅ Test message sent")
            except Exception as e:
                logger.warning(f"⚠️ Test message failed: {e}")
            
            # Register event handler
            @self.client.on(events.NewMessage(chats=self.source_id))
            async def message_handler(event):
                await self.process_message(event.message)
            
            logger.info("🔄 Copier is now running! Waiting for messages...")
            
            # Process recent messages
            try:
                logger.info("📋 Checking recent messages...")
                async for message in self.client.iter_messages(self.source_id, limit=5):
                    await self.process_message(message, is_backlog=True)
            except Exception as e:
                logger.error(f"Error processing backlog: {e}")
            
            while self.is_running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            raise
    
    async def process_message(self, message, is_backlog=False):
        """Process and filter a message before copying"""
        try:
            if not message.text and not message.media:
                return
            
            content = message.text or ""
            
            # Filter by keywords
            if INCLUDE_KEYWORDS:
                content_lower = content.lower()
                has_keyword = False
                for keyword in INCLUDE_KEYWORDS:
                    if keyword.lower() in content_lower:
                        has_keyword = True
                        break
                if not has_keyword:
                    return
            
            if EXCLUDE_KEYWORDS:
                content_lower = content.lower()
                for keyword in EXCLUDE_KEYWORDS:
                    if keyword.lower() in content_lower:
                        return
            
            # Apply replacements
            modified_content = content
            for old_word, new_word in REPLACEMENTS.items():
                modified_content = modified_content.replace(old_word, new_word)
            
            # Copy message
            if message.media:
                await self.client.send_file(
                    self.dest_id,
                    message.media,
                    caption=modified_content,
                    parse_mode='html'
                )
                logger.info(f"✅ Copied media (ID: {message.id})")
            else:
                await self.client.send_message(
                    self.dest_id,
                    modified_content,
                    parse_mode='html'
                )
                logger.info(f"✅ Copied text (ID: {message.id})")
                
            if is_backlog:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Error: {e}")
    
    def stop(self):
        self.is_running = False

async def main():
    copier = TelegramCopier()
    try:
        await copier.start()
    except KeyboardInterrupt:
        logger.info("👋 Stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal: {e}")

if __name__ == "__main__":
    asyncio.run(main())
