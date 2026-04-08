from langgraph.graph import StateGraph,START,END
from typing import TypedDict,Annotated
from langchain_huggingface import HuggingFaceEndpoint,ChatHuggingFace
from langchain_core.messages import BaseMessage,HumanMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_google_genai import  ChatGoogleGenerativeAI
import sqlite3

config={'configurable':{'thread_id':'2'}}
 



llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash"
)

class ChatState(TypedDict):
    messages:Annotated[list[BaseMessage],add_messages]


def chat_node(state:ChatState):
    messages=state['messages']
    response=llm.invoke(messages).content
    return {'messages':[response]}

conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)
checkpointer=SqliteSaver(conn=conn)

graph=StateGraph(ChatState)
graph.add_node('chat_node',chat_node)
graph.add_edge(START,'chat_node')
graph.add_edge ('chat_node',END)

chatbot = graph.compile(checkpointer=checkpointer)

def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])

    return list(all_threads)