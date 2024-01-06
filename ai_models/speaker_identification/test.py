from clova_speech import ClovaSpeechClient
from postprocessing import speaker_diarization, get_star_voice
import json

if __name__ == '__main__':
    # file path
    audio_path = "data/raw_audio/test_30s.m4a"
    timestamp_file_path = "data/clova_results/test.json"
    output_path = "data/star_audio/output.wav"

    # clova ai model 통해서 화자식별
    res = ClovaSpeechClient().req_upload(file=audio_path, completion='sync')
    test = json.loads(res.text)
    with open(timestamp_file_path, 'w') as outfile:
        json.dump(test, outfile)

    # 식별된 각 화자 중 고인의 목소리를 선택하여 추출
    selected_speaker_id = 1
    speaker_num, speech_list = speaker_diarization(timestamp_file_path)
    final_clip = get_star_voice(audio_path, speech_list, selected_speaker_id)

    # audio file로 저장
    final_clip.export(output_path, format="wav")


    