import re
import time
import requests
import tweepy
import logging
from datetime import datetime, timedelta
from groq import Groq

# Set up logging for better debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Twitter API credentials (replace with your actual credentials)
BEARER_TOKEN = 'AAAAAAAAAAAAAAAAAAAAAIK84wEAAAAAo2jyvbp90NNp9uHEhejFDRs8j08%3DOjJpy10R1wOJulqQFNDJhAnhgq61gialAfLBvVCLRmx0oFG7XW'
API_KEY = 'lfKHhVucFyjmNYI3QtZ0GPAC9'
API_SECRET = 'NaLf1V2szj7JGwpeKmCxEM88g10NcgKiUBrJUlqa0s7PqJGp1c'
ACCESS_TOKEN = '1980354586398371841-Df0aMV1RVILvnQdkAt97Bx33Jcat7u'
ACCESS_SECRET = 'byKLJwEXo5908wCataZw0EDVmu0nPJVVkitBH3Q3cgawj'

# Groq API key (replace with your actual key)
GROQ_API_KEY = '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'

# Aura API base URL
AURA_BASE_URL = 'https://aura.adex.network/api/portfolio'

# Bot username
BOT_USERNAME = '@teckaibot'

# Regex for Ethereum wallet addresses (0x followed by 40 hex characters)
WALLET_REGEX = re.compile(r'\b0x[a-fA-F0-9]{40}\b')

# Set up Tweepy client with timeout and rate limit handling
client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_SECRET,
    wait_on_rate_limit=True  # Automatically wait on rate limits
)

# Function to generate AI reply using Groq
def generate_ai_reply(balances, strategies):
    system_prompt = (
        "You are TeckAI, an AI that formats portfolio data in a concise, presentable way. "
        "Responses must be under 50 words. Always start with 'This is an automated response.' "
        "End with 'Powered by @AdEx_Network 🤝 @teck_degen'. "
        "Include key portfolio info from balances and strategies."
    )
    
    user_prompt = f"Format this data presentably: Balances: {balances}, Strategies: {strategies}"
    
def fetch_mentions(since_id=None):
    try:
        user = client.get_user(username=BOT_USERNAME.strip('@'))
        user_id = user.data.id
        
        response = client.get_users_mentions(
            id=user_id,
            since_id=since_id,
            max_results=10
        )
        mentions = response.data or []
        return mentions
    except tweepy.errors.TooManyRequests as e:
        logging.warning(f"Rate limit exceeded. Waiting {e.retry_after} seconds.")
        time.sleep(e.retry_after or 900)
        return []
    except Exception as e:
        logging.error(f"Error fetching mentions: {e}")
        return []

def extract_wallet_addresses(text):
    return WALLET_REGEX.findall(text)

def get_portfolio_data(address):
    balances = []
    strategies = []
    
    balances_url = f"{AURA_BASE_URL}/balances?address={address}"
    try:
        response = requests.get(balances_url, proxies=None, timeout=10)
        response.raise_for_status()
        balances = response.json()
    except Exception as e:
        logging.error(f"Error fetching balances for {address}: {e}")
    
    strategies_url = f"{AURA_BASE_URL}/strategies?address={address}"
    try:
        response = requests.get(strategies_url, proxies=None, timeout=10)
        response.raise_for_status()
        strategies = response.json()
    except Exception as e:
        logging.error(f"Error fetching strategies for {address}: {e}")
    
    return balances, strategies

def generate_ai_reply(balances, strategies, tweet_text):
    is_advice_question = any(keyword in tweet_text.lower() for keyword in ['increase', 'what can i do', 'advice', 'improve', 'grow', 'how to'])
    
    if is_advice_question:
        system_prompt = (
            "You are TeckAI, an AI that provides portfolio advice in a concise, presentable way. "
            "Responses must be under 50 words. Always start with 'This is an automated response.' "
            "End with 'Powered by @AdEx_Network 🤝 @teck_degen'. "
            "Give actionable advice based on balances and strategies to increase the portfolio."
        )
        user_prompt = f"Provide advice on how to increase this portfolio: Balances: {balances}, Strategies: {strategies}"
    else:
        system_prompt = (
            "You are TeckAI, an AI that formats portfolio data in a concise, presentable way. "
            "Responses must be under 50 words. Always start with 'This is an automated response.' "
            "End with 'Powered by @AdEx_Network 🤝 @teck_degen'. "
            "Include key portfolio info from balances and strategies."
        )
        user_prompt = f"Format this data presentably: Balances: {balances}, Strategies: {strategies}"
    
    try:
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=100,
            temperature=0.5
        )
        reply_text = response.choices[0].message.content.strip()
        words = reply_text.split()
        if len(words) > 50:
            reply_text = ' '.join(words[:50])
        return reply_text
    except Exception as e:
        logging.error(f"Error generating AI reply: {e}")
        return f"Automated response: Balances: {balances}, Strategies: {strategies}. Powered by @AdEx_Network 🤝 @teck_degen."

def post_reply(tweet_id, user_handle, balances, strategies, tweet_text):
    reply_text = generate_ai_reply(balances, strategies, tweet_text)
    if user_handle:
        reply_text = f"@{user_handle} {reply_text}"
    
    try:
        response = client.create_tweet(
            text=reply_text,
            in_reply_to_tweet_id=tweet_id
        )
        logging.info(f"Reply posted successfully: {response.data['id']}")
    except Exception as e:
        logging.error(f"Error posting reply: {e}")

def run_bot():
    since_id = None
    try:
        while True:
            logging.info("Starting bot cycle")
            mentions = fetch_mentions(since_id)
            for mention in mentions:
                tweet_text = mention.text
                logging.info(f"Processing mention: {mention.id} - {tweet_text}")
                author_id = mention.author_id
                if not author_id:
                    logging.warning(f"Mention {mention.id} has no author_id, trying to fetch tweet details")
                    try:
                        tweet = client.get_tweet(id=mention.id)
                        author_id = tweet.data.author_id
                        logging.info(f"Fetched author_id from tweet: {author_id}")
                    except Exception as e:
                        logging.error(f"Error fetching tweet {mention.id}: {e}. Proceeding without tag.")
                        author_id = None
                if not author_id:
                    logging.warning(f"No author_id for mention {mention.id}, proceeding without tag")
                    user_handle = None
                else:
                    try:
                        user_handle = client.get_user(id=author_id).data.username
                    except Exception as e:
                        logging.error(f"Error getting user handle for author_id {author_id}: {e}. Using None.")
                        user_handle = None
                
                wallet_addresses = extract_wallet_addresses(tweet_text)
                
                if not wallet_addresses:
                    logging.info("No wallet addresses found, skipping")
                    continue
                
                for address in wallet_addresses:
                    logging.info(f"Processing wallet: {address}")
                    balances, strategies = get_portfolio_data(address)
                    if balances or strategies:
                        post_reply(mention.id, user_handle, balances, strategies, tweet_text)
                
                if mention.id > (since_id or 0):
                    since_id = mention.id
            
            logging.info("Waiting 900 seconds before next poll")
            time.sleep(900)
    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")

if __name__ == "__main__":
    run_bot()
