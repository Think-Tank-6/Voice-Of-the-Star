import tiktoken

def token_count(text,gpt_version):
    if gpt_version == 'gpt3.5':
        model_encoding = "gpt-3.5-turbo-16k-0613"
    elif gpt_version == 'gpt4':
        model_encoding = "gpt-4-0613"
    else:
        raise ValueError("버전을 잘못 입력하셨습니다.")
    
    encoding = tiktoken.encoding_for_model(model_encoding)
    
    
    response_token = encoding.encode(text)
       
    total_tokens = len(response_token)

    return total_tokens

def load_text_from_bottom(text, max_token, gpt_version):
    lines = text.split('\n')[::-1]

    total_lines = []
    token_sum = 0
    for line in lines:
        new_text = line + '\n'
        tok = token_count(new_text, gpt_version)
        token_sum += tok
    
        if token_sum > max_token:
            break

        total_lines.append(line)

    # 리스트를 뒤집고, 각 줄을 개행 문자('\n')로 연결
    return '\n'.join(total_lines[::-1])