import os
import re

def get_user_name(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            if '님과 카카오톡 대화' in line:
                user_name = line.split('님과 카카오톡 대화')[0].strip()
                return user_name.strip('\ufeff')
    return None

def extract_messages(filename, user_name):
    messages = []
    pattern_app = re.compile(rf'^.*,\s*{re.escape(user_name)}\s*:\s*(.*)$')
    pattern_pc = re.compile(rf'^\[{re.escape(user_name)}\]\s*\[.*\]\s*(.*)$')
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            match_app = pattern_app.search(line)
            match_pc = pattern_pc.search(line)
            if match_app:
                messages.append(match_app.group(1).strip())
            elif match_pc:
                messages.append(match_pc.group(1).strip())
    return messages

def save_messages(messages, output_filename):
    with open(output_filename, 'w', encoding='utf-8') as file:
        for message in messages:
            file.write(message + '\n')

input_directory = 'input/'
output_directory = 'output/'


for filename in os.listdir(input_directory):
    if filename.endswith('.txt'):
        full_input_path = os.path.join(input_directory, filename)
        user_name = get_user_name(full_input_path)

        if user_name:
            user_messages = extract_messages(full_input_path, user_name)
            if user_messages:
                full_output_path = os.path.join(output_directory, f'extracted_messages_{filename}')
                save_messages(user_messages, full_output_path)


