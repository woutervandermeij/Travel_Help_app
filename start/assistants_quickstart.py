from openai import OpenAI
import shelve
from dotenv import load_dotenv
import os
import time

BASEDIR = os.path.abspath(os.path.dirname(__file__))
print(BASEDIR)
load_dotenv(os.path.join(BASEDIR, ".env"),override=True)

OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")
client = OpenAI(api_key=OPEN_AI_API_KEY)
print(OPEN_AI_API_KEY )


# --------------------------------------------------------------
# Upload file
# --------------------------------------------------------------
def upload_file(path):
    # Upload a file with an "assistants" purpose
    file = client.files.create(file=open(path, "rb"), purpose="assistants")
    return file


file = upload_file("../data/airbnb-faq-test.pdf")


# --------------------------------------------------------------
# Create assistant
# --------------------------------------------------------------
def create_assistant(file):
    #"""
    #You currently cannot set the temperature for Assistant via the API.
    #"""
    assistant = client.beta.assistants.create(
        name="WhatsApp AirBnb Assistant",
        instructions="You're a helpful WhatsApp assistant that can assist guests that are staying in our Paris AirBnb. Use your knowledge base to best respond to customer queries. If you don't know the answer, say simply that you cannot help with question and advice to contact the host directly. Be friendly and funny.",
        tools=[{"type": "retrieval"}],
        model="gpt-4-1106-preview",
      #  file_ids=[file.id],
    )
    return assistant




assistant = create_assistant(file)


#W: Made the assistant to answer the questions. 
assistant = client.beta.assistants.create(
  name="The PDF guy",
  instructions="You are a personal hotel help. Search the PDF to answer questions.",
  tools=[{"type": "file_search"}],
  model="gpt-4o",
  file_ids=[file.id]
)
#--------------------------------------------------------------
# W: Make a vector, to have a chain of documents the AI can read  
#--------------------------------------------------------------
# Create a vector store caled "Hotel Document"
vector_store = client.beta.vector_stores.create(name="Hotel Document")
 
# Ready the files for upload to OpenAI
file_paths = ["../data/airbnb-faq-test.pdf", "../data/3-day_Amsterdam_Guide.pdf"]
file_streams = [open(path, "rb") for path in file_paths]
 
# Use the upload and poll SDK helper to upload the files, add them to the vector store,
# and poll the status of the file batch for completion.
file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
  vector_store_id=vector_store.id, files=file_streams
)
 
# You can print the status and the file counts of the batch to see the result of this operation.
print(file_batch.status)
print(file_batch.file_counts)

#--------------------------------------------------------------
# W: Step 3: Update the assistant to to use the new Vector Store
#--------------------------------------------------------------

assistant = client.beta.assistants.update(
  assistant_id=assistant.id,
  tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
)


# --------------------------------------------------------------
# Thread management
# --------------------------------------------------------------
def check_if_thread_exists(wa_id):
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(wa_id, None)


def store_thread(wa_id, thread_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[wa_id] = thread_id


# --------------------------------------------------------------
# Generate response
# --------------------------------------------------------------
def generate_response(message_body, wa_id, name):
    # Check if there is already a thread_id for the wa_id
    thread_id = check_if_thread_exists(wa_id)

    # If a thread doesn't exist, create one and store it
    if thread_id is None:
        print(f"Creating new thread for {name} with wa_id {wa_id}")
        thread = client.beta.threads.create()
        store_thread(wa_id, thread.id)
        thread_id = thread.id

    # Otherwise, retrieve the existing thread
    else:
        print(f"Retrieving existing thread for {name} with wa_id {wa_id}")
        thread = client.beta.threads.retrieve(thread_id)

    # Add message to thread
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_body,
    )

    # Run the assistant and get the new message
    new_message = run_assistant(thread)
    print(f"To {name}:", new_message)
    return new_message


# --------------------------------------------------------------
# Run assistant
# --------------------------------------------------------------
def run_assistant(thread):
    # Retrieve the Assistant
    assistant = client.beta.assistants.retrieve("asst_03PYWOUSsRv8rdlBwtkCa4Ey")

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )

    # Wait for completion
    while run.status != "completed":
        # Be nice to the API
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    # Retrieve the Messages
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    new_message = messages.data[0].content[0].text.value
    print(f"Generated message: {new_message}")
    return new_message


# --------------------------------------------------------------
# Test assistant
# --------------------------------------------------------------

new_message = generate_response("What's the check in time?", "123", "John")

new_message = generate_response("What's the pin for the lockbox?", "456", "Sarah")

new_message = generate_response("What was my previous question?", "123", "John")

new_message = generate_response("What was my previous question?", "456", "Sarah")

#gives an summary of the day with 20 minutes breaks. Only point 8 of the red light district the naughty AI added. . 
new_message = generate_response("can you give me a fun trip in Amsterdam?", "456", "John")

new_message = generate_response("can you tell me more about the Concertgebouw?", "456", "John")

new_message = generate_response("What about coffeeshops?", "456", "John")

#Great answer only the vondelpark are listed under Nightclubs 
new_message = generate_response("What is the most fun things for a bachelor party?", "456", "John")

#The Wificode
new_message = generate_response("What is the wificode?", "456", "John")


