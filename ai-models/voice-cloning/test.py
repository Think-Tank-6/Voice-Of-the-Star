from xtts import load_model, create_star_vector, inference
import torchaudio

def main():
    model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
    model = load_model(model_name)
    speech_file = "./input/YH_5m_test.wav"
    gpt_cond_latent, speaker_embedding = create_star_vector(model,speech_file)
    text = "안녕하세요! 테스트입니다."
    output = inference(model,text, gpt_cond_latent,speaker_embedding)
    torchaudio.save("./output/en_test_4.wav", output, 24000)

if __name__ == "__main__":
	main()