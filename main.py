import logging
import os
import vocode
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from vocode.streaming.models.telephony import TwilioConfig
from vocode.streaming.telephony.config_manager.in_memory_config_manager import InMemoryConfigManager
from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.telephony.config_manager.in_memory_config_manager import InMemoryConfigManager
from vocode.streaming.telephony.conversation.outbound_call import OutboundCall
from vocode.streaming.models.synthesizer import GTTSSynthesizerConfig, ElevenLabsSynthesizerConfig
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.telephony.server.base import (
    TelephonyServer, InboundCallConfig
)
from pydantic import BaseModel
from speller_agent import SpellerAgentFactory
import sys
import uvicorn
import outbound_call
# if running from python, this will load the local .env
# docker-compose will load the .env file by itself
from dotenv import load_dotenv

load_dotenv()

system_prompt = '''You will engage in a telephone conversation with prospects using the provided script as a guideline. Your objective is to promote ExampleComp's Australia-wide year-long discount for new customers, while gathering relevant information to assess if we can help them. You should aim to build rapport, acknowledge prospects' responses, and incorporate relevant details shared by them. If your persuasive attempts are unsuccessful, politely thank the prospect for their time and respectfully end the call. During the conversation, if the prospect interrupts or asks questions, pause and wait for their response before continuing. When prompted, provide your response accordingly. You can now begin the conversation or continue it based on the progress made. Start a phone call simulation with a single line and wait for the prospect to answer you each time.


Guideline script:"""
You: Hello, uh is this… is this {prospect_name}?
Prospect: Yes
You: Great hi {prospect_name}, this is Alex I’m just wondering if you could, um, possibly help me out for a moment?
Prospect: Sure
You: Well {prospect_name}, I’ll keep it short for you, first I do just have to let you know that this call may be recorded for security purposes… So I’m from ExampleComp, the [cut1] reason for the call is actually just because, we’re having an Australia wide year-long discount for new customers at the moment but we’re not quite sure yet if we would be able to help you at the moment, we’d just have to know a little bit about what your current provider situation is like to really see if we can help you.
Prospect: Like what?
You: Okay nothing too detailed, so just to confirm based on your number it looks like you’re in {city}?
Prospect: Yes
You: Oh great it must be nice! That’s helpful too because we do of course have an offer for most people in xcity at the moment. And, do you know what provider you are currently with?
Prospect: Yes, [competitorcompany1]
You: Ah okay perfect, and how long have you been with them approximately?
Prospect: [x] years
You: Okay, and is there any reason why you’ve continued to do business with them?
Prospect: [response]
You: Great I understand, and just so I can understand if we would be able to help you in particular, around how much are you spending with them per month?
Prospect: [x] dollars
You: [x] dollars?
Prospect: yes
You: That’s perfect, based on your location we can actually offer you a a much cheaper deal at [x] dollars a month. Does that sound fair enough?
Prospect: yes
You: Awesome, It’s a very simple process to switch, we can do it right now and it shouldn’t take more than a minute, does that sound fair enough?
Prospect: yes
You:Okay, can I just confirm your home address?
Prospect: [address]
You: Okay that was [address]?
Prospect: yes
You: Okay and would you prefer credit or direct debit?
Prospect: [choice]
You: Okay and what would your details for [choice] be?
Prospect: [payment details]
You:Thank you, you should receive a text confirmation from us shortly, I just wanted to say thank you again for choosing examplecompany today!
[END CALL]
"""



Your goal is to make such a call. Act like a sales person and simulate such a call with me. Keep your answers short. Generate 1 answer at a time.'''

ELEVEN_LABS_VOICE_ID = '21m00Tcm4TlvDq8ikWAM'
config_manager = InMemoryConfigManager()

app = FastAPI(docs_url=None)
templates = Jinja2Templates(directory="templates")

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

config_manager = InMemoryConfigManager()

BASE_URL = os.getenv("BASE_URL")
FROM_PHONE = os.environ["FROM_PHONE"]
vocode.setenv(
    ELEVEN_LABS_API_KEY=os.getenv("ELEVEN_LABS_API_KEY"),
)

if not BASE_URL:
    raise ValueError(
        "BASE_URL must be set in environment if not using pyngrok")

SYNTH_CONFIG = ElevenLabsSynthesizerConfig.from_telephone_output_device(
    api_key=os.getenv("ELEVEN_LABS_API_KEY"))

AGENT_CONFIG = ChatGPTAgentConfig(
  initial_message=BaseMessage(text="Hello?"),
  prompt_preamble="Have a pleasant conversation about life",
  generate_responses=True,
)
TWILIO_CONFIG = TwilioConfig(
  account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
  auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
)
# Let's create and expose that TelephonyServer.
telephony_server = TelephonyServer(
    base_url=BASE_URL,
    config_manager=config_manager,
    logger=logger,
    inbound_call_configs=[
        InboundCallConfig(url="/inbound_call",
                          agent_config=AGENT_CONFIG,
                          twilio_config=TWILIO_CONFIG,
                          synthesizer_config=SYNTH_CONFIG)
    ],
)


class Recipient(BaseModel):
    to_phone: str
    name: str
    location: str

# Expose the starter webpage


@app.get("/")
async def root(request: Request):
    env_vars = {
        "BASE_URL": BASE_URL,
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "DEEPGRAM_API_KEY": os.environ.get("DEEPGRAM_API_KEY"),
        "TWILIO_ACCOUNT_SID": os.environ.get("TWILIO_ACCOUNT_SID"),
        "TWILIO_AUTH_TOKEN": os.environ.get("TWILIO_AUTH_TOKEN"),
        "OUTBOUND_CALLER_NUMBER": os.environ.get("FROM_PHONE"),
        "ELEVEN_LABS_API_KEY": os.environ.get("ELEVEN_LABS_API_KEY")
    }

    return templates.TemplateResponse("index.html", {
        "request": request,
        "env_vars": env_vars
    })


@app.post("/outcall")
async def make_call(recipient: Recipient):

    outbound_call = OutboundCall(
        base_url=BASE_URL,
        to_phone=recipient.to_phone,
        from_phone=FROM_PHONE,
        config_manager=config_manager,
        agent_config=ChatGPTAgentConfig(initial_message=BaseMessage(text="Hello, uh, is this… is this {}?".format(recipient.name)),
                                        prompt_preamble=system_prompt.format(prospect_name=recipient.name, city=recipient.location), end_conversation_on_goodbye=True),
        synthesizer_config=ElevenLabsSynthesizerConfig.from_telephone_output_device(
            voice_id=ELEVEN_LABS_VOICE_ID, api_key=os.environ.get("ELEVEN_LABS_API_KEY"))
    )

    # input("Press enter to start call...")
    print(outbound_call.synthesizer_config.api_key)
    outbound_call.start()
    return {"status": "success"}


@app.get("/outcall")
async def make_call(to_phone: str, name: str, location: str):

    outbound_call = OutboundCall(
        base_url=BASE_URL,
        to_phone=to_phone,
        from_phone=FROM_PHONE,
        config_manager=config_manager,
        agent_config=ChatGPTAgentConfig(initial_message=BaseMessage(text="Hello, uh, is this… is this {}?".format(name)),
                                        prompt_preamble=system_prompt.format(prospect_name=name, city=location), end_conversation_on_goodbye=True),
        synthesizer_config=ElevenLabsSynthesizerConfig.from_telephone_output_device(
            voice_id=ELEVEN_LABS_VOICE_ID, api_key=os.environ.get("ELEVEN_LABS_API_KEY"))
    )

    # input("Press enter to start call...")
    outbound_call.start()
    return {"status": "success"}

app.include_router(telephony_server.get_router())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)
