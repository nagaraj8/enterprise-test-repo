from slack_sdk import WebClient
from dotenv import load_dotenv
import os

load_dotenv()

client = WebClient(
    token=os.getenv('SLACK_BOT_TOKEN')
)

def fetch_channels():
    response = client.conversations_list()

    return response['channels']