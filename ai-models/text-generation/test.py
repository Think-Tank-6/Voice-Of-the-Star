from preprocessing import get_user_name,save_messages,extract_messages
import os

input_directory = 'input/'
output_directory = 'output/'

if __name__ == '__main__':
    for filename in os.listdir(input_directory):
        if filename.endswith('.txt'):
            full_input_path = os.path.join(input_directory, filename)
            user_name = get_user_name(full_input_path)

            if user_name:
                user_messages = extract_messages(full_input_path, user_name)
                if user_messages:
                    full_output_path = os.path.join(output_directory, f'extracted_messages_{filename}')
                    save_messages(user_messages, full_output_path)