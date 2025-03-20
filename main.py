import io
import os
import json
import PyPDF2
import tiktoken
import requests
from dotenv import load_dotenv
from pydantic import BaseModel
from prompts import fund_information_prompt, portfolio_information_prompt
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv('API_KEY'))

class FundInformation(BaseModel):
    fund_name: str
    aum: str

class Investment(BaseModel):
    company_name: str
    fair_value: float
    maturity_date: str
    reference_rate: str
    asset_type: str
    sector: str

class PortfolioInformation(BaseModel):
    top_investments: list[Investment]

def fetch_document(url: str) -> bytes:
    res = requests.get(url)
    return res.content

def create_reader(document: bytes) -> PyPDF2.PdfReader:
    stream = io.BytesIO(document)
    reader = PyPDF2.PdfReader(stream)
    return reader

def generate_structured(system_prompt: str, message: str, response_format) -> str:
    response = client.beta.chat.completions.parse(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        model="gpt-4o-2024-08-06",
        response_format=response_format
    )
    return response.choices[0].message.content

def generate_text(system_prompt: str, message: str) -> str:
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

def parse_json(input_str: str) -> json:
    try:
        parsed = json.loads(input_str)
        return parsed
    except:
        print("Could not parse your json!")

def find_page_num(pdf_reader: PyPDF2.PdfReader, search_text: str) -> int:
    for i, page in enumerate(pdf_reader.pages):
        text = page.extract_text()
        if search_text.lower() in text.lower():
            return i
    return -1

def process_fund_information(pdf_reader: PyPDF2.PdfReader, structured_output: bool) -> dict:
    search_text = "BLACKSTONE CREDIT & INSURANCE REVIEW"
    page_num = find_page_num(pdf_reader, search_text)
    if page_num == -1:
        raise ValueError("Page not found! Adjust your search.")
    
    fund_information = pdf_reader.pages[page_num].extract_text()
    
    if structured_output:
        extracted_fund = generate_structured(fund_information_prompt, fund_information, FundInformation)
    else:
        extracted_fund = generate_text(fund_information_prompt, fund_information)

    parsed_fund = parse_json(extracted_fund)
    return parsed_fund

def process_portfolio_information(pdf_reader: PyPDF2.PdfReader, structured_output: bool) -> dict:
    search_text = "BCRED TOP PORTFOLIO POSITIONS"
    page_num = find_page_num(pdf_reader, search_text)
    if page_num == -1:
        raise ValueError("Page not found! Adjust your search.")

    portfolio_information = pdf_reader.pages[page_num].extract_text()

    if structured_output:
        extracted_portfolio = generate_structured(portfolio_information_prompt, portfolio_information, PortfolioInformation)
    else:
        extracted_portfolio = generate_text(portfolio_information_prompt, portfolio_information)
    
    parsed_portfolio = parse_json(extracted_portfolio)
    return parsed_portfolio

def combine_results(fund_data: dict, portfolio_data: dict) -> dict:
    combined_result = fund_data.copy()
    combined_result['top_investments'] = portfolio_data['top_investments']
    return combined_result

def main():
    url = "https://www.bcred.com/wp-content/uploads/sites/11/blackstone-secure/BCRED-Overview-Presentation.pdf?v=1733864680"
    structured_output = True

    deck_bytes = fetch_document(url)
    pdf_reader = create_reader(deck_bytes)
        
    fund_data = process_fund_information(pdf_reader, structured_output)
    portfolio_data = process_portfolio_information(pdf_reader, structured_output)
    
    combined_result = combine_results(fund_data, portfolio_data)
    
    return combined_result

if __name__ == "__main__":
    result = main()
    print(json.dumps(result, indent=2))