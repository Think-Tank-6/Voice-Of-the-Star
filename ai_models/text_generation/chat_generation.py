def insert_persona_to_prompt(star_name,relationship,system_input_path):
    with open(system_input_path, 'r', encoding='utf-8') as file:
        system_input = file.read()

    system_input = system_input.replace("[star]",star_name)
    system_input = system_input.replace("[relationship]",relationship)

    return system_input

def merge_prompt_input(characteristics, system_input, text):
    system_prompt = system_input.replace("[chat_style]",characteristics)
    system_prompt = system_prompt + text
    return system_prompt

def prepare_chat(star_name, star_gender, text):
    if star_gender=="M":
        gender_param = "his"
    else:
        gender_param = "her"

    messages = [{'role': 'system', 'content': text}]
    messages.append({'role': 'user', 'content': "From now on, answer like " + star_name + " reflecting " + gender_param + " text characteristics. "})

    return messages

def get_response(client, user_input, messages):
    messages.append({'role': 'user', 'content': user_input})
    response = client.chat.completions.create(
        model="gpt-4-0613",
        top_p=0.1,
        temperature=1,
        messages=messages
    )

    assistant_response = response.choices[0].message.content
    messages.append({'role': 'assistant', 'content': assistant_response})

    return assistant_response, messages
