from dotenv import load_dotenv
from openai import OpenAI
import os
load_dotenv()

API_KEY = os.getenv("GPT_API_KEY")
client = OpenAI(api_key=API_KEY)
def detect_voice_phishing(client,user_input,prompt):
    
    #gpt 구현
    messages = []
    messages.append({'role': 'system', 'content': prompt})

    messages.append({'role': 'user', 'content': user_input})
              
    response = client.chat.completions.create(
        model= "gpt-3.5-turbo-16k-0613",
        top_p=0,
        temperature=0,
        messages=messages
    )

    assistant_response = response.choices[0].message.content
    return assistant_response
    

if __name__ == '__main__':

    user_input = "엄마 어디예요?"
    prompt_path = "C:/Users/82102/dev/vos_project/VOS-server/backend/app/ai_models/text_generation/prompt_data/crime_prevention.txt"
   
    with open(prompt_path,"r") as file:
        prompt = file.read()


    output = detect_voice_phishing(client,user_input,prompt)
