import os
import openai
import PyPDF2
import tiktoken
import json
from typing import List
from prompts import value_extractor, commentary_generator
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

def open_text_file(file_path: str) -> str:
    with open(file_path, 'r') as file:
        content = file.read()
    return content

def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    return len(tokens)

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

def chunk_document(input_document: str, max_tokens: int = 3000) -> List:
    words = input_document.split(" ")
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        token_count = count_tokens(word)
        if current_length + token_count > max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(word)
        current_length += token_count

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def find_relevant_chunks(chunks: List, keywords: List=["commercial paper"]) -> List:
    relevant_chunks = []
    for chunk in chunks:
        if all(keyword.lower() in chunk.lower() for keyword in keywords):
            relevant_chunks.append(chunk)
    return relevant_chunks
    
def run_agent(document_text: str, max_tokens: int, keywords: List, system_prompt: str):
    raw_chunks = chunk_document(document_text, max_tokens=max_tokens)
    relevant_chunks = find_relevant_chunks(raw_chunks, keywords=keywords)
    if not relevant_chunks:
        raise Exception(f"No relevant chunks found! Update the agent parameters!")
    
    combined_context = "\n\n".join(relevant_chunks)
    context_tokens = count_tokens(combined_context)
    system_tokens = count_tokens(system_prompt)
    
    total_tokens = context_tokens + system_tokens
    if total_tokens > 4096 * .95:
        raise Exception(f"Context of {total_tokens} too large! Change the max_tokens in the chunker!")

    try:
        response = generate_text(system_prompt, combined_context)
        parsed_response = json.loads(response)
        return parsed_response
    except:
        return None
    
def extract_commercial_debt():
    document_text = extract_text_from_pdf('./input.pdf')

    value_agent = {
        "max_tokens": 1500,
        "keywords": ['commercial paper', 'current liabilities', 'balance sheet'],
        "system_prompt": value_extractor
    }
    value_data = run_agent(document_text, **value_agent)
    if not value_data:
        raise Exception("Your value agent did not return any information!")

    commentary_agent = {
        "max_tokens": 1800,
        "keywords": ['commercial paper', 'repurchase agreements'],
        "system_prompt": commentary_generator
    }
    commentary_data = run_agent(document_text, **commentary_agent)
    if not commentary_data:
        raise Exception("Your commentary agent did not return any information!")

    return {
        "commercial_debt": value_data.get("commercial_debt", 0),
        "commentary": commentary_data.get("commentary", "No commercial paper program or commercial paper debt was mentioned in the provided 10K excerpt.")
    }
        
if __name__ == "__main__":
    commercial_paper = extract_commercial_debt()
    print(json.dumps(commercial_paper, indent=4))