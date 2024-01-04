from preprocessing import get_user_name, extract_messages

if __name__ == '__main__':

    file_content = ""

    user_name = get_user_name(file_content)

    if user_name:
        user_messages = extract_messages(file_content, user_name)
