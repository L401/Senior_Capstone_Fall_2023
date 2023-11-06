"""
PDF Content Extractor and Analyzer, 

Description:
This script provides an simnple rule based solution for extracting various content types from a PDF document. It can:
- Extract and categorize text based on font details and it's order. 
- Extract images from the PDF and recognize text using the Tesseract OCR engine.
- Extract tables in a structured format.

The content extraction is facilitated by a combination of the `PyPDF2`, `pdfminer`, `pdfplumber`, and `pytesseract` libraries. 
The results are saved in a structured JSON format and should only be viewed in JSON.

Features:
1. Text extraction based on detailed font properties.
2. Image extraction and Optical Character Recognition (OCR) using Tesseract.
3. Table extraction in a structured format.

Usage:
1. Ensure the Tesseract OCR engine is installed and the path (`TESSERACT_PATH`) is correctly set.
2. Specify the target PDF file path (`PDF_PATH`).
3. Run the script to process the PDF and save the extracted data in a JSON format.

Note:
- Temporary files generated during processing (e.g., cropped images) are automatically deleted post-processing.

Author: Zachary Knapp
Date: 11/2/23
Version: 3.0
"""

# TODO: 25 character limit, continue to aggregate text

import PyPDF2
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTFigure
import pdfplumber
from PIL import Image
from pdf2image import convert_from_path
import pytesseract
import os
import json
import numpy as np
from collections import defaultdict

# Define constants
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
PDF_PATH = "./data/AFD-180201-00-5-3.pdf"

# Initialize script
print("[INFO] Initializing...")
print(f"[INFO] Using Tesseract at {TESSERACT_PATH}")
print(f"[INFO] Processing PDF from {PDF_PATH}")


# Set Tesseract command and open PDF with pdfplumber
def initialize_pdf(PDF_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    return pdfplumber.open(PDF_PATH)


# Clear the content of the extracted data file
with open(r"./data/extracted_data.txt", "w") as file:
    pass


def normalize_fontname(fontname):
    if fontname == "Times-Italic":
        return "Times-Roman"
    return fontname


def extract_text(element):
    word_formats = []
    formatted_text = []
    last_font_detail = None
    current_text = ""

    subheaders_and_contents = {}
    current_subheader = None

    for text_line in element:
        if isinstance(text_line, LTTextContainer):
            words = text_line.get_text().split()
            word_index = 0
            for character in text_line:
                if isinstance(character, LTChar):
                    font_detail = (
                        normalize_fontname(character.fontname),
                        round(float(character.size), 2),
                    )
                    if word_index < len(words):
                        word = words[word_index]
                        if character.get_text() == word[0]:
                            if font_detail != last_font_detail:
                                if last_font_detail is not None:
                                    formatted_text.append(
                                        (last_font_detail, current_text.strip())
                                    )

                                    # Check if it's a subheader or content
                                    if len(formatted_text) % 2 == 0:  # It's content
                                        subheaders_and_contents[
                                            current_subheader
                                        ] = current_text.strip()
                                    else:  # It's a subheader
                                        current_subheader = current_text.strip()

                                last_font_detail = font_detail
                                current_text = ""
                                if font_detail not in word_formats:
                                    word_formats.append(font_detail)
                            current_text += word + " "
                            word_index += 1

    # Store the text of the last font detail
    if last_font_detail is not None:
        formatted_text.append((last_font_detail, current_text.strip()))

        # Last item logic
        if len(formatted_text) % 2 == 0:  # It's content
            subheaders_and_contents[current_subheader] = current_text.strip()
        else:  # It's a subheader with no associated content
            subheaders_and_contents[current_text.strip()] = ""

    with open(r"./data/extracted_data.txt", "a", encoding="utf-8") as file:
        file.write(f"\nWord Formats: {word_formats}\n")
        for subheader, content in subheaders_and_contents.items():
            file.write(f"Subheading: {subheader}\nContent: {content}\n")

    return word_formats, subheaders_and_contents


# Gather all font data from the PDF
def gather_all_font_data(PDF_PATH):
    font_data = []
    print("[INFO] Gathering font data from PDF...")

    for page in extract_pages(PDF_PATH):
        text_elements = [e for e in page if isinstance(e, LTTextContainer)]

        for element in text_elements:
            _, format_per_line = extract_text(element)
            font_data.extend(format_per_line)
    print(f"[DEBUG] Total number of font data points: {len(font_data)}")
    return font_data


# Crop an image element from a PDF page
def crop_image(element, pageObj):
    print("[DEBUG] Inside crop_image function.")
    print(f"[DEBUG] Cropping coordinates:")

    # Get the coordinates to crop the image from the PDF
    [image_left, image_top, image_right, image_bottom] = [
        element.x0,
        element.y0,
        element.x1,
        element.y1,
    ]
    # Crop the page using coordinates (left, bottom, right, top)
    pageObj.mediabox.lower_left = (image_left, image_bottom)
    pageObj.mediabox.upper_right = (image_right, image_top)
    # Save the cropped page to a new PDF
    cropped_pdf_writer = PyPDF2.PdfWriter()
    cropped_pdf_writer.add_page(pageObj)
    # Save the cropped PDF to a new file
    with open("cropped_image.pdf", "wb") as cropped_pdf_file:
        cropped_pdf_writer.write(cropped_pdf_file)


# Convert a PDF page to an image
def convert_to_image(input_file):
    print("[DEBUG] Inside convert_to_image function.")
    print("[DEBUG] Image saved as PDF_image.png")

    images = convert_from_path(input_file)
    images[0].save("PDF_image.png", "PNG")


# Extract text from an image using Tesseract OCR
def extract_text_from_image(image_path):
    print("[DEBUG] Inside extract_text_from_image function.")

    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    img.close()
    return text


# Extract table from PDF
def extract_table_from_pdf(PDF_PATH, pagenum, table_num):
    print("[DEBUG] Inside extract_table_from_pdf function.")
    with initialize_pdf(PDF_PATH) as pdf:
        table_page = pdf.pages[pagenum]
        return table_page.extract_tables()[table_num]


# Convert table data to a structured string format
def convert_table_to_string(table):
    print("[DEBUG] Inside convert_table_to_string function.")

    table_string = ""
    for row in table:
        cleaned_row = [
            item.replace("\n", " ")
            if item is not None and "\n" in item
            else "None"
            if item is None
            else item
            for item in row
        ]
        table_string += "|" + "|".join(cleaned_row) + "|" + "\n"
    return table_string[:-1]


# Extract data from PDF
pdfFileObj = open(PDF_PATH, "rb")
pdfReader = PyPDF2.PdfReader(pdfFileObj)
text_per_page = {}


# Extract and process images from a given PDF page
def extract_and_process_images(
    pageObj_from_pdfminer, pdfReader, pagenum, page_elements
):
    print("[INFO] Extracting images...")
    print(f"[DEBUG] Number of page elements: {len(page_elements)}")

    pageObj_from_pypdf2 = pdfReader.pages[pagenum]
    images_text = []

    for i, component in enumerate(page_elements):
        _, element = component

        if isinstance(element, LTFigure):
            # Handle Image
            crop_image(element, pageObj_from_pypdf2)
            convert_to_image("cropped_image.pdf")
            image_text = extract_text_from_image("PDF_image.png")
            images_text.append(image_text)
    return images_text


# Extract tables from a given PDF page and return them as text
def process_tables(page, pagenum, pdf):
    print("[INFO] Extracting tables from PDF...")

    table_texts = []

    page_tables = pdf.pages[pagenum]
    tables = page_tables.find_tables()

    for table_num in range(len(tables)):
        table = extract_table_from_pdf(pdf, pagenum, table_num)
        table_string = convert_table_to_string(table)
        table_texts.append(table_string)
    return table_texts


# Process a single PDF page to extract and categorize its content
def process_page(page, pdfReader, pdf, pagenum):
    print(f"[INFO] Processing Page {pagenum + 1}...")

    page_content = {
        "subheading": {},
        "images": [],
        "tables": [],
    }

    current_subheading = None

    page_elements = [(element.y1, element) for element in page._objs]
    page_elements.sort(key=lambda a: a[0], reverse=True)

    page_content["images"] = extract_and_process_images(
        page, pdfReader, pagenum, page_elements
    )

    for _, element in page_elements:
        if isinstance(element, LTTextContainer):
            _, extracted_texts_dict = extract_text(element)
            page_content["subheading"].update(extracted_texts_dict)

    page_content["tables"] = process_tables(page, pagenum, pdf)
    return page_content


# Convert extracted data from PDF pages to a structured format
def structure_pdf_data(text_per_page):
    print("[INFO] Structuring extracted data...")
    data = []

    for page_num, content_dict in text_per_page.items():
        page_data = {
            "document_id": "",
            "document_title": "",
            "document_url": PDF_PATH,
            "page_number": f"Page_{page_num}",
            "subheader": content_dict.get("subheading", {}),
            "table_text": "\n".join(content_dict.get("tables", [])),
            "image_text": "\n".join(content_dict.get("images", [])),
            "vector": "<BERT_Embedding_of_combined_text>",
            "traceability": {
                "source": "Tinker Air Force Base",
                "manual_reference": "",
                "exact_location": f"n{page_num}",
            },
        }
        data.append(page_data)

    return data


# Save structured data to a JSON file
def save_data_to_json(data, path="./data/extracted_data.json"):
    print(f"[INFO] Saving extracted data to JSON file")
    with open(path, "w") as f:
        json.dump(data, f, indent=4)
    print("[INFO] Data successfully saved to JSON")


def output_to_txt(filename, format_data, text_data):
    with open(
        filename, "a"
    ) as f:  # Use 'a' to append to the file, so that you can write multiple lines without overwriting previous content.
        f.write("Line Formats: " + str(format_data) + "\n")
        f.write("Line Text: " + text_data + "\n\n")  # Two newlines for separation.


def main():
    print("[INFO] Starting main execution...")

    with open(PDF_PATH, "rb") as pdfFileObj:
        pdfReader = PyPDF2.PdfReader(pdfFileObj)
        print("[DEBUG] Initializing PDF...")
        pdf = initialize_pdf(PDF_PATH)
        text_per_page = {}
        print("[DEBUG] Gathering all font data...")
        font_data = gather_all_font_data(PDF_PATH)

        # Loop through all the pages of the PDF
        for pagenum, page in enumerate(extract_pages(PDF_PATH)):
            print(f"[DEBUG] Processing page number {pagenum + 1}...")
            # Process the content of the current page
            page_content = process_page(page, pdfReader, pdf, pagenum)
            # Store the processed content into the text_per_page dictionary
            text_per_page[f"Page_{pagenum}"] = page_content
        print("[DEBUG] Cleaning up temporary files...")
        try:
            os.remove("cropped_image.pdf")
        except FileNotFoundError:
            pass
        try:
            os.remove("PDF_image.png")
        except FileNotFoundError:
            pass

        print("[DEBUG] Structuring processed PDF data...")
        processed_data = structure_pdf_data(text_per_page)
        print("[DEBUG] Saving processed data to JSON...")
        save_data_to_json(processed_data)
        pdf.close()
        print("[INFO] Completed!")


if __name__ == "__main__":
    main()
