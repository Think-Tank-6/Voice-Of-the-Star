
import base64
from dotenv import load_dotenv
from fastapi import HTTPException
from openai import OpenAI
import os

from ai_models.voice_cloning.xtts import create_star_vector, load_model
from ai_models.text_generation.preprocessing import get_user_name,extract_messages
from ai_models.text_generation.token_limit import load_text_from_bottom
from ai_models.text_generation.characteristic_generation import merge_prompt_text,get_characteristics
from ai_models.text_generation.chat_generation import insert_persona_to_prompt,merge_prompt_input,get_response,prepare_chat
from ai_models.speaker_identification.clova_speech import ClovaSpeechClient
from ai_models.speaker_identification.postprocessing import speaker_diarization
from ai_models.text_generation.crime_prevention import detect_voice_phishing

import json
from io import BytesIO
import base64
from pydub import AudioSegment
import pickle

load_dotenv()

# Model Load
VOICE_CLONING_MODEL_PATH = os.getenv("VOICE_CLONING_MODEL_PATH")
voice_cloning_model = load_model(VOICE_CLONING_MODEL_PATH)


### Load GPT ###
class PromptGeneration:
    API_KEY = os.getenv("GPT_API_KEY")
    client = OpenAI(api_key=API_KEY)

    def __init__(self, request,original_text) -> None:

        self.original_text = original_text
        self.star_gender = request["gender"]
        self.star_name = request["star_name"]
        self.persona = request["persona"]
        self.relationship = request["relationship"]

        self.API_KEY = os.getenv("GPT_API_KEY")
        self.client = OpenAI(api_key=self.API_KEY)

        self.prompt_file_path = os.getenv("PROMPT_FILE_PATH")
        self.system_input_path = os.getenv("SYSTEM_INPUT_PATH")

    def create_prompt_input(self) -> str:
               
        user_name = get_user_name(self.original_text)
        print("user_name : ", user_name)
        star_text = extract_messages(self.original_text, user_name)
      
        star_text_12k = load_text_from_bottom(star_text, 12000,'gpt3.5')
        star_text_4k = load_text_from_bottom(star_text, 4000,'gpt4')
               
        # process for extracting characteristics
        prompt = merge_prompt_text(star_text_12k,self.prompt_file_path)
        characteristics = get_characteristics(prompt,self.client)
        
        # process for preparing system prompt
        system_input = insert_persona_to_prompt(self.star_name,self.relationship,self.system_input_path)
        chat_prompt_input_data = merge_prompt_input(characteristics,system_input,star_text_4k)
        
        return chat_prompt_input_data

    
class SpeakerIdentification:
    COMBINED_STAR_VOICE_FILE_PATH = os.getenv("COMBINED_STAR_VOICE_FILE_PATH")

    def get_speaker_samples(self,original_voice_file):
        audio_byte = BytesIO(original_voice_file.file.read())
        audio_seg = AudioSegment.from_file(audio_byte)

        audio_binary = audio_seg.export(format="wav").read()
        res = ClovaSpeechClient().req_upload(file=audio_binary, completion='sync')
        timestamp = json.loads(res.text)

        speaker_num, speech_list, speaker_sample_list = speaker_diarization(timestamp)
        # speaker_sample_list에 담긴 타임스탬프 이용해서 original_voice_file의 각 구간을 byteio로 변환
        for key in speaker_sample_list.keys():
            speaker_info = speaker_sample_list[key]
            
            segment = audio_seg[int(speaker_info['start']):int(speaker_info['end'])]
            buffer = BytesIO()
            segment.export(buffer, format="wav")
            audio_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            buffer.seek(0)
            speaker_sample_list[key]["audio_byte"] = audio_base64

        original_voice_base64 = base64.b64encode(audio_byte.getvalue()).decode("utf-8")

        return speaker_num, speech_list, speaker_sample_list, original_voice_base64

    def save_star_voice(self,selected_speaker_id, speech_list, original_voice_base64, star_id):
        # speech_list 가져와서 고인 목소리 이어붙이는 작업
        decoded_base64 = base64.b64decode(original_voice_base64)
        original_voice_byte_file = BytesIO(decoded_base64)
        audio_segment = AudioSegment.from_file(original_voice_byte_file)
        combined_star_voice_file = audio_segment[0:0]
        for v in speech_list[selected_speaker_id]:
            combined_star_voice_file += audio_segment[int(v['start']):int(v['end'])]
            
        save_file_path = self.COMBINED_STAR_VOICE_FILE_PATH + f"/{star_id}_combined_voice_file.wav"
        combined_star_voice_file.export(save_file_path, format="wav")


class VoiceCloning:

    def get_star_voice_vector(self, star_id: int):
        
        COMBINED_STAR_VOICE_FILE_PATH = os.getenv("COMBINED_STAR_VOICE_FILE_PATH")
        combined_star_voice_file = COMBINED_STAR_VOICE_FILE_PATH + f"/{star_id}_combined_voice_file.wav"

        gpt_cond_latent, speaker_embedding = create_star_vector(
            voice_cloning_model, 
            combined_star_voice_file
        )

        try:
            if not os.path.exists(combined_star_voice_file):
                raise HTTPException(status_code=404, detail="File not found")
            
            os.remove(combined_star_voice_file)
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")
        
        gpt_cond_latent_pkl = pickle.dumps(gpt_cond_latent)
        speaker_embedding_pkl = pickle.dumps(speaker_embedding)
        
        return gpt_cond_latent_pkl, speaker_embedding_pkl
    

class ChatGeneration:
    API_KEY = os.getenv("GPT_API_KEY")
    client = OpenAI(api_key=API_KEY)

    def __init__(self, p_data, messages):
        self.messages = messages
        self.p_data = p_data

        self.messages.insert(0,{'role': 'system', 'content': p_data})

    def get_gpt_answer(self,user_input):
        self.messages.append({'role': 'user', 'content': user_input})
        gpt_answer = get_response(self.client,self.messages)
        self.messages.append({'role': 'assistant', 'content': gpt_answer})

        return gpt_answer, self.messages
    

class DetectCrime:
    API_KEY = os.getenv("GPT_API_KEY")
    client = OpenAI(api_key=API_KEY)

    def __init__(self,voice_phishing_p_data_path):
        with open(voice_phishing_p_data_path,"r",encoding='utf-8') as f:
            self.voice_phishing_p_data = f.read()

    def detect_voice_phishing_activity(self,text_input) -> bool:

        gpt_answer = detect_voice_phishing(self.client,text_input,self.voice_phishing_p_data)

        if "Yes" in gpt_answer or "yes" in gpt_answer:
            is_detected = True
        else:
            is_detected = False

        return is_detected