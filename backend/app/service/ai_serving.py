
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

from ai_models.text_generation.preprocessing import get_user_name,extract_messages
from ai_models.text_generation.token_limit import load_text_from_bottom
from ai_models.text_generation.characteristic_generation import merge_prompt_text,get_characteristics
from ai_models.text_generation.chat_generation import insert_persona_to_prompt,merge_prompt_input

### Load GPT ###
class TextGeneration:
    API_KEY = os.getenv("GPT_API_KEY")
    client = OpenAI(api_key=API_KEY)

    def __init__(self, request,original_text_file) -> None:
        
        self.original_text_file = original_text_file
        self.star_gender = request["gender"]
        self.star_name = request["star_name"]
        self.persona = request["persona"]
        self.relationship = request["relationship"]

        self.API_KEY = os.getenv("GPT_API_KEY")
        self.client = OpenAI(api_key=self.API_KEY)

        # 추후 수정
        self.prompt_file_path = 'prompt_data/extract_characteristic.txt'
        self.system_input_path = "prompt_data/system_input.txt"

    def create_prompt_input(self,original_text_file) -> str:

        text = original_text_file.read()
        decoded_text = text.decode("utf-8")
               
        user_name = get_user_name(decoded_text)
        if user_name:
            star_text = extract_messages(decoded_text, user_name)
      
        star_text_12k = load_text_from_bottom(star_text, 12000,'gpt3.5')
        star_text_4k = load_text_from_bottom(star_text, 4000,'gpt4')
               
        # process for extracting characteristics
        prompt = merge_prompt_text(star_text_12k,self.prompt_file_path)
        characteristics = get_characteristics(prompt,self.client)
        
        # process for preparing system prompt
        system_input = insert_persona_to_prompt(self.star_name,self.relationship,self.system_input_path)
        chat_prompt_input_data = merge_prompt_input(characteristics,system_input,star_text_4k)
        
        return chat_prompt_input_data
