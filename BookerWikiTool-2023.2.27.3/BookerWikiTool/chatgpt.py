import openai
import os
import traceback

def chatgpt_cmd(args):
    # Set your API key
    openai.api_key = args.openai_token
    while True:
        try:
            ipt = input('chatgpt> ')
            if ipt.strip().lower() == 'exit':
                break
            # Use the GPT-3 model
            completion = openai.Completion.create(
                engine="text-davinci-002",
                prompt=ipt,
                max_tokens=1024,
                temperature=0.5
            )
            # Print the generated text
            print(completion.choices[0].text)
        except KeyboardInterrupt: break
        except:
            traceback.print_exc()

