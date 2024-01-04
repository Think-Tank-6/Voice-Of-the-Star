from extract_characteristics import load_GPT, merge_prompt_text, get_characteristics

if __name__ == '__main__':

    ### file path ###
    prompt_file_path = 'prompt_data/extract_characteristic.txt'
    text = "" # user's text (str)

    ### load model ###
    client = load_GPT()

    ### process for extracting characteristics ###
    prompt = merge_prompt_text(text,prompt_file_path)
    response = get_characteristics(prompt,client)

    

    