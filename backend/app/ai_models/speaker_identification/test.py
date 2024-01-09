from clova_speech import ClovaSpeechClient
from postprocessing import speaker_diarization, get_star_voice
import json
from io import BytesIO
from pydub import AudioSegment

if __name__ == '__main__':
    # file path
    audio_path = "data/raw_audio/test_15s.m4a"
    timestamp_file_path = "data/clova_results/test.json"
    output_path = "data/star_audio/output.wav"

    # 식별된 각 화자 중 고인의 목소리를 선택하여 추출
    selected_speaker_id = 1

    # clova ai model 통해서 화자식별
    res = ClovaSpeechClient().req_upload(file=audio_path, completion='sync')
    timestamp = json.loads(res.text)
    speaker_num, speech_list, speaker_sample_list = speaker_diarization(timestamp, audio_path) #speaker_sample_list -> 각 화자의 음성파일리스트
    # final_clip = audio_segment[0:0]
    # for v in selected_voice:
    #     final_clip += audio_segment[int(v['start']):int(v['end'])]

    # final_clip = get_star_voice(audio_path, speech_list, selected_speaker_id) 
    # final_clip.export(output_path, format="wav") # wav로만 저장


