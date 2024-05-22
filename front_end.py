import time
import streamlit as st
import pandas as pd
from openai import OpenAI
from geopy.geocoders import Nominatim
import re

# Initialize geolocator
geolocator = Nominatim(user_agent="geoapidemo")

pd.set_option('display.max_colwidth', None)

def get_openai_response(message_text, assistant_id):
    """Generates response from OpenAI assistant"""
    # OpenAI API key
    api_key = "INSERT API KEY"

    # OpenAI Model
    assistant_id = assistant_id

    # Create client
    client = OpenAI(api_key=api_key)

    # Create thred with message
    thread = client.beta.threads.create(
    messages=[
        {
        "role": "user",
        "content": message_text,
        }
    ]
    )
    print(f"OpenAI thread {thread.id}")

    # Submit the thread to the assistant
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)
    print(f"OpenAI run created {run.id}")
    while run.status != "completed":
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        print('run.status:', run.status)
        time.sleep(2)

    message_response = client.beta.threads.messages.list(thread_id=thread.id)
    message_response_data = message_response.data
    latest_response = message_response_data[0]
    print(f"Final AI response: {latest_response.content[0].text.value}")
    return(latest_response.content[0].text.value)

# Define 
country_text = "Produce a very concise summary (using a maximum of 4 bullet points and one short paragraph) of trends in influenza using the provided data, there should be a bullet discussing the situation in key countries such as Australia and the USA, with the summary covering the whole world. Do not include information or trends about other diseases."

# Import
df = pd.read_csv("news_output.csv")
filtered_df = df[df['outbreak'] == 'TRUE']
# Import
new_df = pd.read_csv("llm_news_detail.csv")

def sentence_caps(text):
    sentences = re.split(r'(?<=[.!?]) +', text)
    return ' '.join(sentence[0].upper() + sentence[1:] if len(sentence) > 0 else '' for sentence in sentences)

def plot_metrics(name, df):
    st.subheader(sentence_caps(name)) # Apply sentence_caps for consistency

    name_2, countries, cases, description, sentiment, outbreak, deaths, region = get_key_metrics(df, name)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Number of Cases", 
              value=int(float(cases)), 
              delta_color="inverse", 
              help="The number of estimated cases based on news reports", 
              label_visibility="visible")
    
    with col2:
        st.metric(label="Number of Deaths", 
              value=int(float(deaths)), 
              delta_color="inverse", 
              help="The number of estimated deaths based on news reports", 
              label_visibility="visible")
        
    with col3:
        if outbreak == "TRUE":
            st.error("Potential outbreak")

    with col4:
        new_filtered_df = new_df[new_df['outbreak_name']==name]
        percentage = new_filtered_df['negative_sentiment']
        percentage = int(float(percentage))
        st.error(f"{percentage}% negative coverage")

def get_key_metrics(df, name):
    '''
    df: processed, labelled, clustered dataset from Newscatcher
    '''
    filtered_df = df[df['name']==name].head(1)
    countries = filtered_df['Country'].to_string(index = False)
    cases = filtered_df['cases'].to_string(index = False)
    description = filtered_df['description'].to_string(index = False)
    sentiment = filtered_df['sentiment'].to_string(index = False)
    outbreak = filtered_df['outbreak'].to_string(index = False)
    deaths = filtered_df['deaths'].to_string(index = False)
    region = filtered_df['region'].to_string(index = False)

    return (name, countries, cases, description, sentiment, outbreak, deaths, region)

def gen_description(name, df):
    name, countries, cases, description, sentiment, outbreak, deaths, region = get_key_metrics(df, name)

    return description

def get_coordinates(location):
    try:
        loc = geolocator.geocode(location)
        return (loc.latitude, loc.longitude, 100)
    except:
        return (None, None, 100)
    
def get_region(name, df):
    name, countries, cases, description, sentiment, outbreak, deaths, region = get_key_metrics(df, name)
    split_region_list = region.split("; ")
    location_list = []
    for region in split_region_list:
        location = get_coordinates(region)
        location_list.append(location)
    coords_to_plot = pd.DataFrame(location_list, columns=['lat', 'lon', 'pointsize'])
    return coords_to_plot

def get_impact(name, df):
    filtered_df = df[df['outbreak_name']==name]
    impact_text = filtered_df['impacts'][0]
    return impact_text

def main():

    if 'country_api_response' not in st.session_state:
        st.session_state['country_api_response'] = None
    if 'comparison_api_response' not in st.session_state:
        st.session_state['comparison_api_response'] = None
    if 'news_api_response' not in st.session_state:
        st.session_state['news_api_response'] = None

    # Set page configuration
    page_bg_color = "#ffffff"  # White background color
    st.markdown(
        f"""
        <style>
        .reportview-container {{
            background-color: {page_bg_color};
            color: black;  /* Black text color */
            font-family: Arial, sans-serif;  /* Arial font */
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    st.title('Global Influenza Dashboard')

    st.header('Weekly briefing')

    # Button to trigger the API call
    if st.button("Generate", key="generate_country"):
        # Make the API call
        st.session_state['country_api_response'] = get_openai_response(country_text, assistant_id="asst_gRJghD8ztvGJj8ygALa8QfnN")
        print("country_api_response", st.session_state['country_api_response'])

    # Always display the API response if it's available
    if st.session_state['country_api_response']:
        if "error" in st.session_state['country_api_response']:
            st.error(st.session_state['country_api_response']["error"])
        else:
            st.write(st.session_state['country_api_response'])

    if st.session_state['country_api_response']:
        # Text input for user messages
        user_input = st.text_input("Your message:", key="user_input_main")

        # Button to send user message
        if st.button("Send", key="send_user_message_country"):        
            # Send the request and get the response
            chat_api_response = get_openai_response(user_input, assistant_id="asst_gRJghD8ztvGJj8ygALa8QfnN")

            # Display bot's response
            st.text_area("AI assistants response:", value=chat_api_response, height=200)

    st.header('Daily news insights')
    
    # Add Key metrics
    if st.button("Extract", key="extract_news"):
        st.session_state['news_api_response'] = True
    
    if st.session_state['news_api_response'] == True:
        time.sleep(5)

        # Pt 1 - Avian influenza
        plot_metrics("Avian influenza", filtered_df)
        avian_description = gen_description("Avian influenza", filtered_df)
        with st.container():
            st.write(avian_description)
        avian_impact = get_impact("Avian influenza", new_df)
        with st.container():
            st.write(f'Impact: {avian_impact}')

        coords_to_plot = get_region("Avian influenza", filtered_df)

        # Display map
        st.subheader('Location of reports') 
        st.map(coords_to_plot, size='pointsize')


        # Pt 2 - swine flu
        plot_metrics("swine flu", filtered_df)
        swine_flu_description = gen_description("swine flu", filtered_df)
        with st.container():
            st.write(swine_flu_description)
        
        coords_to_plot = get_region("swine flu", filtered_df)

        # Display map
        st.subheader('Location of reports') 
        st.map(coords_to_plot, size='pointsize')

    if st.session_state['country_api_response'] and st.session_state['news_api_response']:

        st.header('Historical comparison and level of consern')
        
        # Prompt
        comparison_text = f"Current Flu Status: {st.session_state['country_api_response']}, Data from the latest news: {filtered_df.to_xml()}"
        # Button to trigger the API call
        if st.button("Generate", key="generate_comparison"):
            print("comparison_text", comparison_text)
            # Make the API call
            st.session_state['comparison_api_response'] = get_openai_response(comparison_text, assistant_id="asst_1S7RkCvxX7lyIKQdP96LjbYm")

            # Display the API response in a text box
        if st.session_state['comparison_api_response']:
            if "error" in st.session_state['comparison_api_response']:
                st.error(st.session_state['comparison_api_response']["error"])
            else:
                st.write(st.session_state['comparison_api_response'])

        # Text input for user messages
        comparison_chat_test = st.text_input("Chat:", key="user_input_comparison")

        # Button to send user message
        if st.button("Send", key="send_user_message_comparison"):
            # Send the request and get the response
            chat_api_response = get_openai_response(comparison_chat_test, assistant_id="asst_1S7RkCvxX7lyIKQdP96LjbYm")

            # Display bot's response
            st.text_area("AI assistants response:", value=chat_api_response, height=200)

if __name__ == '__main__':
    main()