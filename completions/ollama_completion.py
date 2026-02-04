import os
# from langchain_community.chat_models import ChatOllama
# from langchain_ollama import ChatOllama
import time
import dotenv

# from kindo_api import KindoAPI
# from openai import OpenAI
from openrouter import call_openrouter


dotenv.load_dotenv()

# def ask_vllm(model_name, query):
#     openai_api_key = "EMPTY"
#     openai_api_base = "http://localhost:8000/v1"
#     client = OpenAI(
#         api_key=openai_api_key,
#         base_url=openai_api_base,
#     )
#     completion = client.completions.create(
#         model=model_name, 
#         messages=[
#             {
#                 "role": "system",
#                 "content": "You are a useful assisstant that can help me with user's questions."
#             },
#             {
#                 "role": "user",
#                 "content": query
#             }
#         ]
#     )

#     return completion.choices[0].message.content

# def ask_chatollama(model_name, query):
#     llm = ChatOllama(
#         model=model_name,
#         base_url=os.getenv("OLLAMA_URL"),
#         temperature=0,
#     )
#     messages=[
#         (
#             "system",
#             "You are a useful assisstant that can help me with user's questions."
#         ),
#         (
#             "user",
#             query
#         )
#     ]
#     response = llm.invoke(messages).content
#     return response

# def ask_kindo(model_name, query):
#     kindo = KindoAPI(os.getenv("KINDO_API_KEY"))
#     response = kindo.call_kindo_api(
#         model=model_name,
#         messages=[
#             {
#                 "role": "system",
#                 "content": "You are a useful assisstant that can help me with user's questions."
#             },
#             {
#                 "role": "user",
#                 "content": query
#             }
#         ],
#     )

#     response = response.json()['choices'][0]['message']['content']

#     return response

def ask_openrouter(model_name, query):
    messages=[
        {
            "role": "system",
            "content": "You are a useful assisstant that can help me with user's questions."
        },
        {
            "role": "user",
            "content": query
        }
    ]
    response = call_openrouter(model_name, messages)
    return response