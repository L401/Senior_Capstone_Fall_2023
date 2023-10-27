"""
PDF Content Extractor and Analyzer, Simple Stat variation

Description:
This script is designed to extract and categorize various content types from a PDF document including 
text (categorized into headings, subheadings, and general content), images, and tables. The categorization 
of text is achieved by analyzing the distribution of font sizes across the document and categorizing based 
on deviation from the mean font size.

Features:
1. Text extraction and categorization based on a simple, fixed font size distribution.
2. Image extraction and Optical Character Recognition (OCR) using Tesseract.
3. Table extraction in a structured format.

Usage:
Ensure the Tesseract OCR engine is installed and the path (`TESSERACT_PATH`) is correctly set. 
Specify the target PDF file path (`PDF_PATH`) and run the script.

Note:
- Extracted images and other temporary files are cleaned up post-processing.
- Results are saved in a JSON format.

Author: Zachary Knapp
Date: 10/26/23
Version: 1.0
"""

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


# Define constants
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
PDF_PATH = "./data/AFD-180201-00-5-3.pdf"

# Initialize script
print("[INFO] Initializing...")
print(f"[INFO] Using Tesseract at {TESSERACT_PATH}")
print(f"[INFO] Processing PDF from {PDF_PATH}")

heading_count = 0
subheading_count = 0
content_count = 0


# Set Tesseract command and open PDF with pdfplumber
def initialize_pdf(PDF_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    return pdfplumber.open(PDF_PATH)


# Clear the content of the extracted data file
with open(r"extracted_data.txt", "w") as file:
    pass


# Extract text and associated font details from an element
def extract_text(element):
    line_text = element.get_text()
    line_formats = []

    for text_line in element:
        if isinstance(text_line, LTTextContainer):
            for character in text_line:
                if isinstance(character, LTChar):
                    font_detail = (
                        character.fontname,
                        round(float(character.size), 2),
                    )  # Rounded to 2 decimal places
                    if font_detail not in line_formats:
                        line_formats.append(font_detail)

    with open(
        r"extracted_data.txt",
        "a",
        encoding="utf-8",
    ) as file:
        file.write(f"Line Formats: {line_formats}\n")
        file.write(f"Line Text: {line_text}\n\n")

    return line_text, line_formats


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


##############################
#   SIMPLE STAT STRATEGY


def categorize_text_based_on_dist(line_text, format_per_line, mean_size, std_dev):
    global heading_count, subheading_count, content_count
    # Default category for text
    category = "content"

    # Retrieve the font size of the text
    if format_per_line:
        current_size = format_per_line[0][1]
        print(f"[DEBUG] Current font size: {current_size}")

        # Determine the category based on deviation from mean font size
        # If the current font size is much larger than the average, classify as a heading
        if current_size > (mean_size + 1 * std_dev):
            category = "heading"
            heading_count += 1
        # If the font size is somewhat larger than the average but not as large as a heading, classify as a subheading
        elif mean_size + 0.25 * std_dev < current_size <= (mean_size + 1 * std_dev):
            category = "subheading"
            subheading_count += 1
        # Otherwise, categorize as content
        else:
            content_count += 1

    print(f"[DEBUG] Predicted category: {category}")
    return {category: line_text}


def calculate_mean_and_std_dev(font_data):
    print("[INFO] Calculating font metrics...")

    # Extract all font sizes from the given data
    font_sizes = [data[1] for data in font_data]

    # Mean and standard deviation
    mean_size = np.mean(font_sizes)
    std_dev = np.std(font_sizes)

    # Median and IQR
    q25 = np.percentile(font_sizes, 25)
    q50 = np.percentile(font_sizes, 50)
    q75 = np.percentile(font_sizes, 75)
    iqr = q75 - q25

    print(f"[DEBUG] Mean font size: {mean_size}")
    print(f"[DEBUG] Standard deviation: {std_dev}")
    print(f"[DEBUG] Median font size: {q50}")
    print(f"[DEBUG] IQR: {iqr}")

    return q50, iqr  # Return median and IQR


# def categorize_text_based_on_dist(line_text, format_per_line, mean_size, std_dev):
#     global heading_count, subheading_count, content_count
#     # Default category for text
#     category = "content"

#     # Retrieve the font size of the text
#     if format_per_line:
#         current_size = format_per_line[0][1]
#         print(f"[DEBUG] Current font size: {current_size}")

#         # Categorize the text based on deviation from mean size
#         if current_size > (mean_size + 2 * std_dev):
#             category = "heading"
#             heading_count += 1
#         elif current_size > (mean_size + 1 * std_dev):
#             category = "subheading"
#             subheading_count += 1
#         else:
#             content_count += 1

#     print(f"[DEBUG] Predicted category: {category}")
#     return {category: line_text}


# def calculate_mean_and_std_dev(font_data):
#     print("[INFO] Calculating mean and standard deviation of font sizes...")

#     font_sizes = [data[1] for data in font_data]
#     mean_size = np.mean(font_sizes)
#     std_dev = np.std(font_sizes)

#     print(f"[DEBUG] Mean font size: {mean_size}")
#     print(f"[DEBUG] Standard deviation: {std_dev}")

#     return mean_size, std_dev


##############################


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


# Categorize and extract text from page elements
def categorize_and_extract_text(page_elements):
    print("[DEBUG] Inside categorize_and_extract_text function.")
    return categorize_text_based_on_dist(page_elements)


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
def process_page(page, pdfReader, pdf, pagenum, mean_size, std_dev):
    print(f"[INFO] Processing Page {pagenum + 1}...")

    page_content = {
        "heading": [],
        "subheading": [],
        "content": [],
        "images": [],
        "tables": [],
    }

    page_elements = [(element.y1, element) for element in page._objs]
    page_elements.sort(key=lambda a: a[0], reverse=True)

    page_content["images"] = extract_and_process_images(
        page, pdfReader, pagenum, page_elements
    )

    for _, element in page_elements:
        if isinstance(element, LTTextContainer):
            line_text, format_per_line = extract_text(element)
            categorized = categorize_text_based_on_dist(
                line_text, format_per_line, mean_size, std_dev
            )

            for category, text in categorized.items():
                page_content[category].append(text)

    page_content["tables"] = process_tables(page, pagenum, pdf)
    return page_content


# Convert extracted data from PDF pages to a structured format
def structure_pdf_data(text_per_page):
    print("[INFO] Structuring extracted data...")
    print(f"[DEBUG] Total number of pages processed: {len(text_per_page)}")
    print("[INFO] Saving data to JSON...")

    data = []

    for page_num, content_dict in text_per_page.items():
        page_data = {
            "document_id": "",
            "document_title": "",
            "document_url": PDF_PATH,
            "page_number": page_num,
            "header": "\n".join(content_dict.get("heading", [])),
            "subheader": "\n".join(content_dict.get("subheading", [])),
            "content": "\n".join(content_dict.get("content", [])),
            "table_text": "\n".join(content_dict.get("tables", [])),
            "image_text": "\n".join(content_dict.get("images", [])),
            "vector": "<BERT_Embedding_of_combined_text>",
            "traceability": {
                "source": "Tinker Air Force Base",
                "manual_reference": "",
                "exact_location": page_num,
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


def main():
    print("[INFO] Starting main execution...")

    with open(PDF_PATH, "rb") as pdfFileObj:
        pdfReader = PyPDF2.PdfReader(pdfFileObj)
        print("[DEBUG] Initializing PDF...")
        pdf = initialize_pdf(PDF_PATH)
        text_per_page = {}
        print("[DEBUG] Gathering all font data...")
        font_data = gather_all_font_data(PDF_PATH)
        print("[DEBUG] Calculating mean and standard deviation of font sizes...")
        mean_size, std_dev = calculate_mean_and_std_dev(font_data)
        for pagenum, page in enumerate(extract_pages(PDF_PATH)):
            print(f"[DEBUG] Processing page number {pagenum + 1}...")
            page_content = process_page(
                page, pdfReader, pdf, pagenum, mean_size, std_dev
            )
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
        print(f"[INFO] Total Headings: {heading_count}")
        print(f"[INFO] Total Subheadings: {subheading_count}")
        print(f"[INFO] Total Content Predictions: {content_count}")
        print("[INFO] Completed!")


if __name__ == "__main__":
    main()
