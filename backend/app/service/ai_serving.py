
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

from ai_models.text_generation.preprocessing import get_user_name,extract_messages
from ai_models.text_generation.token_limit import load_text_from_bottom
from ai_models.text_generation.characteristic_generation import merge_prompt_text,get_characteristics
from ai_models.text_generation.chat_generation import insert_persona_to_prompt,merge_prompt_input,get_response,prepare_chat
from ai_models.speaker_identification.clova_speech import ClovaSpeechClient
from ai_models.speaker_identification.postprocessing import speaker_diarization

import json
from io import BytesIO
from pydub import AudioSegment

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

        # 추후 수정
        self.prompt_file_path = os.getenv("PROMPT_FILE_PATH")
        self.system_input_path = os.getenv("SYSTEM_INPUT_PATH")

    def create_prompt_input(self) -> str:
               
        user_name = get_user_name(self.original_text)
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
            buffer.seek(0)

            speaker_sample_list[key]["audio_byte"] = buffer
            
        return speaker_num, speech_list, speaker_sample_list

    def save_star_voice(self,selected_speaker_id, speech_list, original_voice_byte_file,star_id):
        # speech_list 가져와서 고인 목소리 이어붙이는 작업
        audio_segment = AudioSegment.from_file(original_voice_byte_file)
        combined_star_voice_file = audio_segment[0:0]
        for v in speech_list[selected_speaker_id]:
            combined_star_voice_file += audio_segment[int(v['start']):int(v['end'])]
        combined_star_voice_file.export(f"{star_id}_combined_voice_file.wav", format="wav")

    


class ChatGeneration:
    API_KEY = os.getenv("GPT_API_KEY")
    client = OpenAI(api_key=API_KEY)

    def __init__(self,user_input,p_data, messages):
        self.user_input = user_input
        self.p_data = p_data
        self.messages = messages

    def get_gpt_answer(self) -> str:
        
        # GPT에 대화 히스토리 넣고 답변 받기
        messages = prepare_chat(self.p_data)
        gpt_answer, messages = get_response(self.client,self.user_input, self.messages)
        
        return gpt_answer, messages
    

class DetectCrime:
    API_KEY = os.getenv("GPT_API_KEY")
    client = OpenAI(api_key=API_KEY)

    def __init__(self,voice_phishing_p_data):
        self.voice_phishing_p_data = voice_phishing_p_data

    def detect_voice_phishing(self,text_input) -> bool:
        
        # 함수이름 수정 필요
        gpt_answer = get_response(self.client,text_input,self.voice_phishing_p_data)

        if "Yes" in gpt_answer or "yes" in gpt_answer:
            is_detected = True
        else:
            is_detected = False

        return is_detected