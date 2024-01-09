import json
from pydub import AudioSegment


# 화자 분리하여 화자별 음성파일리스트 생성
def speaker_diarization(timestamp_file_path):

    with open(timestamp_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    speech_list = {}

    for seg in data['segments']:
        cur_speaker_id = int(seg['diarization']['label'])
        if cur_speaker_id in speech_list:
            speech_list[cur_speaker_id].append({'speaker_id':cur_speaker_id,'start':seg['start'],'end':seg['end'],'confidence':seg['confidence']})
        else:
            speech_list[cur_speaker_id] = [{'speaker_id':cur_speaker_id,'start':seg['start'],'end':seg['end'],'confidence':seg['confidence']}]
    
    speaker_num = speech_list.keys
    
    return speaker_num, speech_list


def get_star_voice(audio_path, speech_list, selected_speaker_id):
    selected_voice = speech_list[selected_speaker_id]
    audio_format = audio_path.split(".")[-1]

    audio_segment = AudioSegment.from_file(audio_path, format=audio_format)

    final_clip = audio_segment[0:0]
    for v in selected_voice:
        final_clip += audio_segment[int(v['start']):int(v['end'])]

    return final_clip





