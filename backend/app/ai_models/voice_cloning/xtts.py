from TTS.utils.manage import ModelManager
from TTS.api import TTS
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
from TTS.utils.generic_utils import get_user_data_dir
import os
import torch
import re

def load_model(model_name):
    ModelManager().download_model(model_name)

    model_path = os.path.join(get_user_data_dir("tts"), model_name.replace("/", "--"))

    config = XttsConfig()
    config.load_json(os.path.join(model_path, "config.json"))

    model = Xtts.init_from_config(config)
    model.load_checkpoint(
        config,
        checkpoint_path=os.path.join(model_path, "model.pth"),
        vocab_path=os.path.join(model_path, "vocab.json"),
        eval=True,
        use_deepspeed=False,
    )
    model.cuda()
    return model


def create_star_vector(model, speech_file):
    speaker_wav = speech_file

    try:
        (gpt_cond_latent,speaker_embedding,) = model.get_conditioning_latents(audio_path=speaker_wav, gpt_cond_len=30, gpt_cond_chunk_len=4, max_ref_length=60)
    except Exception as e:
        print("Speaker encoding error", str(e))

    return gpt_cond_latent, speaker_embedding


def inference(model,text, gpt_cond_latent,speaker_embedding):

    prompt = text
    prompt= re.sub("([^\x00-\x7F]|\w)(\.|\。|\?)",r"\1 \2\2",prompt)


    out = model.inference(
                    prompt,
                    "ko",
                    gpt_cond_latent,
                    speaker_embedding,
                    repetition_penalty=5.0,
                    temperature=0.75,
                    speed=1,
                )
    res = torch.tensor(out["wav"]).unsqueeze(0)
    return res
    

