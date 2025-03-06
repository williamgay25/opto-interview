# pip install 

import os
import openai
import PyPDF2
import json
from typing import List
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('API_KEY')
openai.api_key = api_key

def extract_text_from_pdf(pdf_path: str) -> str:
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n"

    return text

def generate_text(system_prompt: str, message: str) -> str:
    response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
        )
    return response.choices[0].message.content

def open_text_file(file_path: str) -> str:
    with open(file_path, 'r') as file:
        content = file.read()
    return content

def chunk_document(document_text: str) -> List:
    words = document_text.split()

    output = []
    chunk = []
    for w in words:
        chunk.append(w)
        if len(chunk) >= 3500:
            output.append(" ".join(chunk))
    
    return output

""" 
NOTE: Naively returns the first instance of commercial paper that is found...
A more thorough approach would be to retrieve all instances and then check for the most accurate.
"""
def extract_information(system_prompt: str, documents: str) -> dict:
    output = []
    for doc in documents:
        #response = generate_text(system_prompt, doc)

        # NOTE: This is just for testing purposes 
        response = '```json\n{\n    "commercial_debt": 0,\n    "commentary": "No commercial paper program or commercial paper debt was mentioned in the provided 10K excerpt."\n}\n```'

        output.append(response)

        parsed_response = json.loads(response)

        if parsed_response["commercial_debt"] != 0:
            return parsed_response

    return {"commercial_debt": 0, "commentary": "No commercial paper program or commercial paper debt was mentioned in the provided 10K excerpt."}

if __name__ == "__main__":
    document_text = extract_text_from_pdf('./input.pdf')
    system_prompt = open_text_file('prompt.txt')
    document_chunks = chunk_document(document_text)

    for chunk in document_chunks:
        commercial_paper = extract_information(chunk, system_prompt)