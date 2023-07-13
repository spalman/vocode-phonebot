import logging
import os
from fastapi import FastAPI
from vocode.streaming.models.telephony import TwilioConfig
from vocode.streaming.telephony.config_manager.in_memory_config_manager import InMemoryConfigManager
from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.telephony.server.base import (
    TelephonyServer,
)
from speller_agent import SpellerAgentFactory
import sys
import uvicorn
import outbound_call
# if running from python, this will load the local .env
# docker-compose will load the .env file by itself
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(docs_url=None)

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

config_manager = InMemoryConfigManager()

BASE_URL = os.getenv("BASE_URL")

# if not BASE_URL:
#     ngrok_auth = os.environ.get("NGROK_AUTH_TOKEN")
#     if ngrok_auth is not None:
#         ngrok.set_auth_token(ngrok_auth)
#     port = sys.argv[sys.argv.index("--port") + 1] if "--port" in sys.argv else 3000

#     # Open a ngrok tunnel to the dev server
#     BASE_URL = ngrok.connect(port).public_url.replace("https://", "")
#     logger.info('ngrok tunnel "{}" -> "http://127.0.0.1:{}"'.format(BASE_URL, port))

if not BASE_URL:
    raise ValueError(
        "BASE_URL must be set in environment if not using pyngrok")

telephony_server = TelephonyServer(
    base_url=BASE_URL,
    config_manager=config_manager,
    agent_factory=SpellerAgentFactory(),
    logger=logger,
)

app.include_router(telephony_server.get_router())
app.include_router(outbound_call.router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
