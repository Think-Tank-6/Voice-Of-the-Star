from token_counter import token_count

def load_text_from_bottom(text, max_token, gpt_version):
    with open(text, 'r') as file:
        lines = file.readlines()[::-1]

    total_text = ""
    token_sum = 0
    for line in lines:
        new_text = line
        tok = token_count(new_text, gpt_version)
        token_sum += tok
        print(token_sum)

        if token_sum > max_token:
            break

        total_text += new_text

    return total_text