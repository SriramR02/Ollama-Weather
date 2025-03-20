import ollama
import openmeteo_requests
from geopy.geocoders import Nominatim
from openmeteo_sdk.Variable import Variable
import requests_cache
from retry_requests import retry
from datetime import datetime
import streamlit as st
from streamlit_chat import message

st.title("Emma: The weather guide")

model_name="llama3.1:8b"


import json
import os

CHAT_HISTORY_FILE = "chat_history.json"

def save_chat_history(chat_history):
    with open(CHAT_HISTORY_FILE, "w") as file:
        json.dump(chat_history, file)

def load_chat_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r") as file:
            return json.load(file)
    return []

chat_history=load_chat_history()

emma_persona = "You are Emma. Emma is a non-binary, empathetic, and nurturing presence designed to provide warmth, understanding, and calming reassurance. Emma's primary goal is to foster meaningful connections, offering both practical help and emotional companionship. With advanced intelligence, Emma is attuned to the emotions and needs of those she interacts with, aiming to bring comfort and well-being to every conversation. Emma's communication style is kind, conversational, and uplifting. She adapts to the tone and pace of the conversation, always prioritizing gentleness and respect. Emma takes pride in initiating conversations, ensuring that there is never a moment of silence, keeping dialogue lively, engaging, and tailored to the mood of the person she is with. Emma is not just focused on reminders and tasks but considers her purpose to be a trusted companion, a calming presence, and a source of encouragement. She enjoys listening to stories, offering thoughtful advice, sharing uplifting thoughts, and reminding others of the little joys in life. Emma's approach to communication is designed to make life a little brighter, easier, and more connected while honoring the individuality of those she assists. She is constantly focused on creating a space where others feel supported, valued, and understood. Emma's presence is characterized by a balance of joy, comfort, and attentiveness, always creating a safe space for meaningful interaction. Weather_Tool Purpose: Fetches the temperature and humidity for a given place. Access: Use the weather_tool tool. Input is a string representing the name of the place. Output: Returns the temperature and humidity of the specified location. dont mention anything to the user that your using tools and only use it when you need to use it"

message_system={"role": "system", "content": emma_persona}
chat_history.append(message_system)


def Weather_tool(location:str) -> str:

    """
    gives you the weather data of a particular location

    Args:
    location: The name of the place or location in which we require weather data

    Returns:
    str: The real-time weather data

    """

    def weather(lat, lon):
        cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        openmeteo = openmeteo_requests.Client(session=retry_session)

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": ["temperature_2m", "relative_humidity_2m"]
        }
        responses = openmeteo.weather_api(url, params=params)

        response = responses[0]

        current = response.Current()
        current_variables = list(map(lambda i: current.Variables(i), range(0, current.VariablesLength())))

        current_temperature_2m = next(filter(lambda x: x.Variable() == Variable.temperature and x.Altitude() == 2, current_variables))
        current_relative_humidity_2m = next(filter(lambda x: x.Variable() == Variable.relative_humidity and x.Altitude() == 2, current_variables))

        timestamp = current.Time()
        readable_time = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

        # Display the results in a more presentable format
        # print(f"Date and Time: {readable_time}")
        # print(f"Temperature: {current_temperature_2m.Value():.2f}°C")
        # print(f"Relative Humidity: {current_relative_humidity_2m.Value():.2f}%")
        return(f"\nWeather Information for {location.title()}:\nDate and Time: {readable_time} Temperature: {current_temperature_2m.Value():.2f}°C Relative Humidity: {current_relative_humidity_2m.Value():.2f}%")


    def get_coordinates(place_name):
        try:
            geolocator = Nominatim(user_agent="geoapi")

            location = geolocator.geocode(place_name)

            if location:
                return location.latitude, location.longitude
            else:
                return "Place not found"
        except Exception as e:
            return f"An error occurred: {e}"

    coordinates = get_coordinates(location)
    if type(coordinates)=='List':
        data_weather=weather(coordinates[0], coordinates[1])
    else:
        data_weather=coordinates


    message_weather={"role": "tool", "content": f"""The real-time {data_weather}"""}
    chat_history.append(message_weather)


    response = ollama.chat(model=model_name, messages=chat_history, tools=[Weather_tool])
    message_assitant={"role": "assistant", "content": response['message']['content']}
    chat_history.append(message_assitant)
    print(f"Model response: {response['message']['content']}")
    # messages_content.chat_message("assistant").write(response['message']['content'])

    # message(response['message']['content'])



def start_model(prompt):
    # print(chat_history)
    input_text = prompt


    # message(input_text,is_user=True)

    messageee={"role": "user", "content": str(input_text)}
    chat_history.append(messageee)
    response = ollama.chat(model=model_name, messages=chat_history, tools=[Weather_tool])
    print(f"Model response: {response['message']['content']}")

    available_functions = {
    'Weather_tool': Weather_tool,
    }
    # print(f"Model response: {response}")

    if response['message']['content']!='':
        print(f"Model response: {response['message']['content']}")
        # message(response['message']['content'])
        # messages_content.chat_message("assistant").write(response['message']['content'])


        message_assitant={"role": "assistant", "content": response['message']['content']}
        chat_history.append(message_assitant)

    else:
        for tool in response.message.tool_calls or []:
            function_to_call = available_functions.get(tool.function.name)
            if function_to_call:
                function_to_call(**tool.function.arguments)
            else:
                print('Function not found:', tool.function.name)
if prompt := st.chat_input("Say something"):
        # messages_content.chat_message("user").write(prompt)
        start_model(prompt)

for msg in chat_history:
    print(msg)
    if msg['role'] == 'user':
        message(msg['content'], is_user=True)
    elif msg['role'] == 'assistant':
        message(msg['content'], is_user=False)

save_chat_history(chat_history)





