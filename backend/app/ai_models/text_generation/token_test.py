from token_limit import load_text_from_bottom

def main():

    file_path = ""
 
  
    result = load_text_from_bottom(file_path,12000,'gpt4')

    print(result)
 
if __name__ == '__main__':
    main()

