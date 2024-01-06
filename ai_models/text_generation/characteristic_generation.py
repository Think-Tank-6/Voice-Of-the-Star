def merge_prompt_text(text,prompt_file_path):
    with open(prompt_file_path, 'r', encoding='utf-8') as file:
        char_prompt = file.read()
    prompt = char_prompt + text    
    return prompt

def get_characteristics(prompt,client):
    
    messages = [{'role': 'system', 'content': prompt}]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo-16k",
        top_p=0.1,
        temperature=0,
        messages=messages
    )

    assistant_response = response.choices[0].message.content

    return assistant_response