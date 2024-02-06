from openai import OpenAI
import os
import dotenv
import time
#from froala_editor import File, Image, S3

#from froala_editor import DjangoAdapter, FlaskAdapter




loaded = dotenv.load_dotenv()  # Assuming .env is in the current directory
print("Environment variables loaded:", loaded)

time.sleep(3)
api_key = "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" #remove after testing
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
logistics_cutoff = 2

assistant_instructions_template_code = os.environ.get("ASSISTANT_INSTRUCTIONS_TEMPLATE")
assistant_instructions_template_nocode = os.environ.get("ASSISTANT_INSTRUCTIONS_TEMPLATE_NOCODE")
assistant_topic = os.environ.get("DEFAULT_ASSISTANT_TOPIC")
MODEL = os.environ.get("MODEL")
Debug = False
thread_id = ""

#print(assistant_instructions_template_code)
#print(assistant_instructions_template_nocode)

def clear_screen():
    if os.name == "nt":
        return os.system("cls")
    else:
        return os.system("clear")


def list_assistants():
    assistants = client.beta.assistants.list()
    print("Please choose one of the following assistants to help you: ")
    count=0
    choice_list = assistants.model_dump()['data']
    #print(choice_list)
    assistant_dict = {}
    new_count=0
    print("****************")
    for assistant in choice_list:
        count += 1 
        if count < len(choice_list)-logistics_cutoff:
            new_count +=1
            if assistant['name'] == None:
                assistant['name'] = "Custom Assistant"
            print(str(new_count) + ": " + assistant['name'])     
            print("****************")
            updater = {new_count: [assistant['name'], assistant['id']]}
            assistant_dict.update(updater)
       
        #print(f"for testing purposes : {choice_list}")
    print("For Custom Assistant, please enter 0.")
    assistant_dict.update({0: ["Custom Assistant", "unknown"]})
    return assistant_dict

def create_custom_assistant(assistant_instructions_template_code, assistant_instructions_template_nocode,model=MODEL):
    topic = input("Please enter a topic for your assistant: ")
    grade_level = int(input("Please enter the grade level of your assistant as a number (example enter \"8\" for 8th Grade): "))
    assistant_instructions = input("Please any custom instructions for your assistant: ")
    assistant_name = str(grade_level).title() +"th grade " + topic.title() + " Master Tutor"
    purpose = input(f"Please enter the purpose of your assistant to fill in this blank 'The Purpose of {assistant_name.title()}is to _______: ")

#    is_code = input("Does your assistant require programming or coding? (y/n): ")
#    if is_code.lower() == "y":
    assistant_instructions_template = assistant_instructions_template_code
#    else:
#        assistant_instructions_template = assistant_instructions_template_nocode
    print(assistant_instructions_template_code)
    assistant_instructions_template = assistant_instructions_template.replace("grade_level", str(grade_level))
    assistant_instructions_template = assistant_instructions_template.replace("topic", topic)
    description = f"The Purpose of {assistant_name.title()} is to {purpose}. It was created by a user to help with {topic} at a {grade_level}th grade level."

    new_assistant = client.beta.assistants.create(instructions=(assistant_instructions_template+assistant_instructions), name=assistant_name, model=MODEL,description=purpose)
    return list_assistants()


def change_settings():
    pass
    
def choose_assistant(assistants):
    while True:
        choice = input("Please choose an assistant: ")
        choice = int(choice)
        if choice == 0:
            assistants = create_custom_assistant(assistant_instructions_template_code, assistant_instructions_template_nocode)
            continue
        elif choice <= len(assistants):
            assistant = assistants[choice]
            assistant_id = assistant[1]
            assistant_name = assistant[0]
            return assistant_name, assistant_id

def improve_input_prompt(prompt):
    #message = create_thread_and_run("asst_RsjhJF9Mm1ZXEDPza8Zo5UR0", prompt)
    #print("Improved Message Reads: ", message)
    return prompt

def create_thread_and_run(assistant_id, message_content):
    if Debug == True:
        print("Creating a thread and running the assistant")
        print("assistant id = ", assistant_id,"message = ",message_content)
    message_content = message_content
    run = client.beta.threads.create_and_run(assistant_id=assistant_id,thread={"messages":[{"role":"user","content": message_content}]})
    run_id = run.id
    thread_id = run.thread_id
    while True:
        reply = run_status(run_id, thread_id)
        if reply:
            return reply

def create_message_and_run(thread_id,assistant_id, message_content):
    if Debug == True:
        print("Creating a message and running the assistant")
        print("Thread id = ",thread_id,"assistant id = ", assistant_id,"message = ",message_content)
    message_content = improve_input_prompt(message_content)
    message = client.beta.threads.messages.create(thread_id=thread_id, role="user", content=message_content)
    reply = create_run(thread_id, assistant_id)
    return reply

def create_run(thread_id, assistant_id):
    run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)
    run_id = run.id
    reply = run_status(run_id, thread_id)
    return reply


def run_status(run_id, thread_id):
    count = 0
    if Debug == True:
        print("Checking the status of the run")
        print("Run id = ", run_id, "Thread id = ", thread_id)
    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        if count % 3 == 1:
            print("*"*30)
            print("Run Status: Working on your Request for thread ", thread_id)
            time.sleep(1)
            print("*"*30)
        else:
            time.sleep(1)
            print("Still Working on It... Please Wait Patiently, OpenAI Servers are taking a while to respond.")
        count += 1
        if run_status.status == "completed":
            print("Run Status: Completed! \n\n\n")
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            reply =messages.data[0].content[0].text.value
            return reply
        
def ask_question(user_question, thread_id, assistant_id, assistant_name, name="You"):
    while user_question.lower() != "quit":
        response = create_message_and_run(thread_id, assistant_id, user_question)
        print(f"{assistant_name} replied: ",end="\n")
        response_list = response.split("\n")
        for line in response_list:
            words = line.split(" ")
            count = 0
            for word in words:
                print(word, end=" ")
                if count >= 20:
                    print("\n")
                    count = 0
                time.sleep(0.1)
                count +=1
            print("\n")
        print("\n")
        print("*"*30)
        print("\n")
        user_response = input(name + ": ")
        user_question = user_response 
        print("\n\n")
        print("*"*30)
        print("\n\n")
        return user_question 
    if user_question.lower() == "quit":
        return print(f"Thank you for using the Ministry of Mastery. \nPlease make sure to save your unique thread {thread_id} so you can continue this conversation where you left off!\nGoodbye!")


def continue_thread(assistant_id, thread_id, assistant_name, name="You"):
    #send welcome message to thread
    #get user input
    print("\n\nDo you have a specific question or would you prefer to start learning from the beggining?")
    print("1: I have a specific question.")
    print("2: I would like to start learning from the beggining.")
    choice = input("Please enter 1 or 2: ")
    while True:
        if choice == "1":
            user_question = input("What would you like to ask " + assistant_name + "? ")
            while True:
                user_question = ask_question(user_question, thread_id, assistant_id, assistant_name, name)
        elif choice == "2":
            user_choice = input(f"Would you like to learn about {assistant_name}'s topic in general, or do you have something specific in mind?")
            if "general" in user_choice.lower():
                user_question = assistant_name + ", I want to learn about your topic in general. Can you please give me a quick assessment of my knowledge about the very basic parts of the topic? I want you to ask me one question and then wait for an answer before asking another. Make sure to give me some feedback and praise, explain what I got wrong and what I answered well, and then ask the next question. After asking 5-6 questions to help you understand what I already know, give me three topics to choose from to start learning. Then explain them following your usual instructions."
                while user_question.lower() != "quit":
                    response = create_message_and_run(thread_id, assistant_id, user_question)
                    print(f"{assistant_name} replied: ",end="")
                    response_list = response.split("\n")
                    for line in response_list:
                        print(line, end="\n")
                        time.sleep(0.1)
                    print("\n")
                    print("*"*30)
                    print("\n")
                    user_response = input(name + ": ")
                    user_question = user_response 
            else:
                user_question = assistant_name + f", I want to learn about your topic in general but more specifically i want to learn about the subtopic {user_choice}. Can you please give me a quick assessment of my knowledge about the very basic parts of the topic? I want you to ask me one question and then wait for an answer before asking another. Make sure to give me some feedback and praise, explain what I got wrong and what I answered well, and then ask the next question. After asking 5-6 questions to help you understand what I already know, give me three topics to choose from to start learning. Then explain them following your usual instructions."
                while user_question.lower() != "quit":
                    response = create_message_and_run(thread_id, assistant_id, user_question)
                    print(f"{assistant_name} replied: ",end="")
                    response_list = response.split("\n")
                    for line in response_list:
                        print(line, end="\n")
                        time.sleep(0.1)
                    print("\n")
                    print("*"*30)
                    print("\n")
                    user_response = input(name + ": ")
                    user_question = user_response 
        else:
            print("Please enter 1 or 2.")
            choice = input("Please enter 1 or 2: ")
            
   

def create_thread():
    thread = client.beta.threads.create()
    print("Save this thread ID to continue this conversation later")
    print("*"*(len(thread.id)+6))
    print("** " + thread.id + " **")
    print("*"*(len(thread.id)+6) + "\n\n\n")
    # Ask the user for the save code
    while True:
        save_code = input("Please enter a save code: ")
        thread_id = thread.id

        if save_code not in open("settings.txt").read(): # Check if the save code is not already in the settings.txt file
            # Open the settings.txt file in append mode
            with open("settings.txt", "a") as file:
            # Write the new line with the format "save_code = thread_id"
                file.write(f"{save_code} = {thread.id}\n")

            print("Save code and thread_id have been saved to settings.txt.")
            return thread.id
        else:
            print("Save code already exists in settings.txt.")
            continue
   


def main(thread_id=""):
    while True:
        #print(assistant_instructions_template_code)
        #print(assistant_instructions_template_nocode)
        print("Do you have a thread you would like to continue? If so, please enter the save code. Otherwise, press enter.")
        save_code_input = input("Please enter your save code to load the thread ID: ")
        if save_code_input :    
            # Initialize a variable to hold the thread_id (assuming it's a string)
            thread_id = None
            # Open the settings.txt file in read mode
            with open("settings.txt", "r") as file:
                # Iterate over each line in the file
                for line in file:
                    # Check if the current line contains the save code
                    if line.startswith(save_code_input):
                        # Extract the thread_id from the line
                        # The line format is expected to be "save_code = thread_id"
                        _, thread_id = line.strip().split(" = ")
                        break  # Exit the loop once the thread_id is found
            # Check if the thread_id was found
            if thread_id:
                print(f"The thread ID for save code '{save_code_input}' is: {thread_id}")
            else:
                print("Save code not found.")
        assistants = list_assistants()
        assistant_name, assistant_id = choose_assistant(assistants)
        clear_screen()
        print("\n\nYou have selected " + assistant_name + " as your assistant. \nPress enter to confirm or type 'no' to choose again.")
        confirm = input()
        if confirm == "no":
            assistant_name, assistant_id = choose_assistant(assistants)
        else:
            clear_screen()
            if thread_id:
                if thread_id.startswith("thread_"):

                    continue_thread(assistant_id, thread_id, assistant_name)
            else:
                thread_id = create_thread()
                continue_thread(assistant_id, thread_id, assistant_name)
            #if input_box.lower() == "quit":
            #    break   
    
    return print(f"Thank you for using the Ministry of Mastery. \nPlease make sure to save your unique thread {thread_id} so you can continue this conversation where you left off!\nGoodbye!")

if __name__ == "__main__":
    clear_screen()
    print("Welcome to the Ministry of Mastery!")
    print("You are welcome to ask one of our master assistants for help.")
    print("We have a few assistants that are Masters in a certain topic.")
    print("We also have a general assistant that can help you with anything \n if there is no master yet for your topic.")   
    time.sleep(1)
    main()