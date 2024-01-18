def detect_voice_phishing(client,user_input,prompt):
    
    #gpt 구현
    messages = []
    messages.append({'role': 'system', 'content': prompt})

    messages.append({'role': 'user', 'content': user_input})
              
    response = client.chat.completions.create(
        model= "gpt-3.5-turbo-16k-0613",
        top_p=0,
        temperature=0,
        messages=messages
    )

    assistant_response = response.choices[0].message.content
    return assistant_response
    

