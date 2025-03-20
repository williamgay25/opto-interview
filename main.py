import os
import io
import openai
import PyPDF2
import tiktoken
import requests
import json
from typing import List
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv('API_KEY'))

def fetch_document(url: str) -> bytes:
    res = requests.get(url)
    return res.content

def create_reader(document: bytes) -> PyPDF2.PdfReader:
    stream = io.BytesIO(document)
    reader = PyPDF2.PdfReader(stream)
    return reader

def generate(system_prompt: str, message: str) -> str:
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        model="gpt-3.5-turbo",
    )
    return response.choices[0].message.content

def extract_text_from_pdf(pdf_path: str) -> str:
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n"

    return text

def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    return len(tokens)

def main():
    url = "https://www.bcred.com/wp-content/uploads/sites/11/blackstone-secure/BCRED-Overview-Presentation.pdf?v=1733864680"
    deck_bytes = fetch_document(url)
    pdf_reader = create_reader(deck_bytes)
    fund_information = pdf_reader.pages[7].extract_text()
    #print(fund_information)

    portfolio_information = pdf_reader.pages[32].extract_text()
    print(portfolio_information)
        
if __name__ == "__main__":
    main()