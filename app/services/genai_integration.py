from dotenv import load_dotenv
load_dotenv()

# Document loaders
from langchain_community.document_loaders import PyPDFLoader

# Text splitters (NEW package)
from langchain_text_splitters import RecursiveCharacterTextSplitter

# LLMs & embeddings
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings
)

# Vector store
from langchain_community.vectorstores import Chroma

# LangChain core
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

# Other
import os
import tempfile
import streamlit as st
import pandas as pd


model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0.1,
)

embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-2.5-flash-lite"
)

# print(model.invoke("value of pi upto 10 decimal places"))
