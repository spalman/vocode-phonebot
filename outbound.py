import vocode
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.models.telephony import CallEntity, TwilioConfig
from vocode.streaming.models.synthesizer import GTTSSynthesizerConfig, ElevenLabsSynthesizerConfig
from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.telephony.hosted.outbound_call import OutboundCall
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.environ["BASE_URL"]


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
vocode.api_key = 'e69621a7d0be1ec12049b60096bd1bed'

if __name__ == '__main__':
    call = OutboundCall(
        recipient=CallEntity(
            phone_number="+61409187317",
        ),
        caller=CallEntity(
            phone_number="+14176143241",
        ),
        agent_config=ChatGPTAgentConfig(initial_message=BaseMessage(text="Hello, uh, is this… is this Flynn?"),
                                        prompt_preamble=system_prompt.format(prospect_name='Flynn', city='Melbourne'), end_conversation_on_goodbye=True),
        twilio_config=TwilioConfig(
            account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
            auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
        ),
        synthesizer_config=ElevenLabsSynthesizerConfig.from_telephone_output_device(
            voice_id=ELEVEN_LABS_VOICE_ID)
    )
    call.start()
    input("Press enter to end the call...")
    call.end()
