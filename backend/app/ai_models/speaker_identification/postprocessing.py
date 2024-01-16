# 화자 분리하여 화자별 음성파일리스트 생성
def speaker_diarization(timestamp):
    speech_list = {}
    speaker_sample_list = {}

    for seg in timestamp['segments']:
        cur_speaker_id = seg['diarization']['label']
        if cur_speaker_id in speech_list.keys():
            speech_list[cur_speaker_id].append({'speaker_id':cur_speaker_id,'start':seg['start'],'end':seg['end'],'confidence':seg['confidence']})
        else:
            speech_list[cur_speaker_id] = [{'speaker_id':cur_speaker_id,'start':seg['start'],'end':seg['end'],'confidence':seg['confidence']}]
    
    speaker_num = len(speech_list.keys())
    speaker_sample_list = {}

    # 화자별 가장 긴 오디오 추출
    for key in list(speech_list.keys()):
        max_speech_time = 0
        for speech in speech_list[key]:
            cur_time = speech['end'] - speech['start']
            if cur_time > max_speech_time:
                max_speech_time = cur_time
                speaker_sample_list[key] = speech
        
    return speaker_num, speech_list, speaker_sample_list




