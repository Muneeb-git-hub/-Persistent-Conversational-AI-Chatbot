# streamlit run chat_bot_with_UI/2_streamlit_streaming.py
import streamlit as st
from langgraph_db_backend import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage
import uuid


# **************utility Function******

def gen_thread():
    thread_id = uuid.uuid4()
    return thread_id


def reset_chat():
    thread_id = gen_thread()
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history'] = []


def add_thread(thread_id):
    if thread_id not in st.session_state['chat_thread']:
        st.session_state['chat_thread'].append(thread_id)


def load_conv(thread_id):
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    return state.values.get('messages', [])


def get_thread_label(thread_id):
    """Get a readable label from the first human message in the thread."""
    if thread_id in st.session_state.get('thread_labels', {}):
        return st.session_state['thread_labels'][thread_id]

    try:
        state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
        messages = state.values.get('messages', [])
        for msg in messages:
            if isinstance(msg, HumanMessage) and msg.content.strip():
                content = msg.content.strip()
                label = (content[:28] + '...') if len(content) > 28 else content
                # Cache it
                if 'thread_labels' not in st.session_state:
                    st.session_state['thread_labels'] = {}
                st.session_state['thread_labels'][thread_id] = label
                return label
    except Exception:
        pass

    return 'New Chat'


# ********session state**************

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = gen_thread()

if 'chat_thread' not in st.session_state:
    st.session_state['chat_thread'] = retrieve_all_threads()

if 'thread_labels' not in st.session_state:
    st.session_state['thread_labels'] = {}

add_thread(st.session_state['thread_id'])


# ************side bar UI*************

st.sidebar.title('LANGGRAPH')

if st.sidebar.button('＋ New Chat', key='new_chat_btn'):
    reset_chat()

st.sidebar.header('Conversation')

for thread_id in st.session_state['chat_thread'][::-1]:
    label = get_thread_label(thread_id)
    is_active = (thread_id == st.session_state['thread_id'])
    display_label = f'▶ {label}' if is_active else f'　{label}'

    if st.sidebar.button(display_label, key=f'thread_{thread_id}'):
        st.session_state['thread_id'] = thread_id
        messages = load_conv(thread_id)

        temp_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = 'user'
            else:
                role = 'assistant'
            temp_messages.append({'role': role, 'content': msg.content})

        st.session_state['message_history'] = temp_messages


# ************main UI****************

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('likh idr')
config = {'configurable': {'thread_id': st.session_state['thread_id']}}

if user_input:
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})

    # Cache label from first user message in this thread
    if st.session_state['thread_id'] not in st.session_state['thread_labels']:
        short = (user_input.strip()[:28] + '...') if len(user_input.strip()) > 28 else user_input.strip()
        st.session_state['thread_labels'][st.session_state['thread_id']] = short

    with st.chat_message('user'):
        st.text(user_input)

    with st.chat_message('AI'):
        ai_message = st.write_stream(
            message_chunk.content
            for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=config,
                stream_mode='messages'
            )
        )
    st.session_state['message_history'].append({'role': 'Ai', 'content': ai_message})