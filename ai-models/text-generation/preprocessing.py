import re

def get_user_name(file_content):
    for line in file_content.splitlines():
        if '님과 카카오톡 대화' in line:
            user_name = line.split('님과 카카오톡 대화')[0].strip()
            return user_name.strip('\ufeff')
    return None

def extract_messages(file_content, user_name):
    messages = []
    pattern_app = re.compile(rf'^.*,\s*{re.escape(user_name)}\s*:\s*(.*)$')
    pattern_pc = re.compile(rf'^\[{re.escape(user_name)}\]\s*\[.*\]\s*(.*)$')
    for line in file_content.splitlines():
        match_app = pattern_app.search(line)
        match_pc = pattern_pc.search(line)
        if match_app:
            messages.append(match_app.group(1).strip())
        elif match_pc:
            messages.append(match_pc.group(1).strip())
    
    messages = '\n'.join(messages)
    return messages