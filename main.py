# pip install -r requirements.txt

import os
import openai
import PyPDF2
import tiktoken
import json
from typing import List
from dotenv import load_dotenv

load_dotenv()

def extract_text_from_pdf(pdf_path: str) -> str:
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n"

    return text

def generate_text(system_prompt: str, message: str) -> str:
    client = openai.OpenAI(
        api_key=os.getenv('API_KEY'),
    )
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        model="gpt-3.5-turbo",
    )
    return response.choices[0].message.content

def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    return len(tokens)

def open_text_file(file_path: str) -> str:
    with open(file_path, 'r') as file:
        content = file.read()
    return content

def find_section(document_text: str) -> List:
    relevant_keywords = ["commercial paper", "short-term borrowings", "debt", "liquidity", "cash equivalents"]

    sections = document_text.split("\n")

    relevant_sections = []
    for section in sections:
        if any(keyword.lower() in section.lower() for keyword in relevant_keywords):
            relevant_sections.append(section)
    
    return relevant_sections

def extract_information(system_prompt: str, document: str) -> dict:
    try:
        response = generate_text(system_prompt, document)
        parsed_response = json.loads(response)
        return parsed_response
    except:
        return {"commercial_debt": 0, "commentary": "No commercial paper program or commercial paper debt was mentioned in the provided 10K excerpt."}

def main():
    document_text = extract_text_from_pdf('./input.pdf')
    system_prompt = open_text_file('prompt.txt')
    document_chunks = find_section(document_text)

    references = []
    print(f'\nStarting extraction for {len(document_chunks)}...')
    for idx, chunk in enumerate(document_chunks):
        print(f'Extracting information for chunk {idx}...')
        commercial_paper = extract_information(chunk, system_prompt)
        if commercial_paper["commercial_debt"] != 0:
            print(f'Found match in chunk {idx}... with output: \n')
            print(json.dumps(commercial_paper, indent=4))
            references.append(commercial_paper)
        
    return references
        
if __name__ == "__main__":
    main()