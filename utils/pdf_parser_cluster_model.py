"""
PDF Content Extractor and Analyzer, Cluster variation

Description:
This script is designed to extract and categorize various content types from a PDF document including 
text (categorized into headings, subheadings, and general content), images, and tables. The categorization 
of text is attempted using kmeans clustering.

Features:
1. Text extraction and categorization based on kmeans clustering.
2. Image extraction and Optical Character Recognition (OCR) using Tesseract.
3. Table extraction in a structured format.

Usage:
Ensure the Tesseract OCR engine is installed and the path (`TESSERACT_PATH`) is correctly set. 
Specify the target PDF file path (`PDF_PATH`) and run the script.

Note:
- Incomplete (logic errors) 
- Extracted images and other temporary files are cleaned up post-processing.
- Results are saved in a JSON format.

Author: Zachary Knapp
Date: 10/26/23
Incomplete
"""


import PyPDF2
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTRect, LTFigure
import pdfplumber
from PIL import Image
from pdf2image import convert_from_path
import pytesseract
import os
import json
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
from collections import Counter

# Set global variable for font_size_clusters
font_size_clusters = None

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
# Using Clusters to predict whether Heading, Subheading, or Content.


def initialize_font_clusters(font_data):
    # Cluster the font metadata using k-means clustering to categorize text sections
    # into three predefined categories: content, subheading, and heading.

    print("[INFO] Initializing font clusters...")

    # Initialize a label encoder for encoding font names into numeric values
    le = LabelEncoder()

    # Transform font names into encoded values
    encoded_font_names = le.fit_transform([name for name, _ in font_data])

    # Extract font sizes
    font_sizes = [size for _, size in font_data]

    # Combine encoded font names and font sizes into a single array
    combined_data = np.array(list(zip(encoded_font_names, font_sizes)))

    # Train a k-means clustering model with 3 clusters
    kmeans = KMeans(n_clusters=3, random_state=0).fit(combined_data)

    # Count the number of data points in each cluster
    cluster_counts = Counter(kmeans.labels_)

    # Sort clusters based on their sizes
    sorted_clusters = sorted(cluster_counts, key=cluster_counts.get)

    # Assign each cluster to a specific category based on its size
    font_clusters = {
        "content": sorted_clusters[2],
        "subheading": sorted_clusters[1],
        "heading": sorted_clusters[0],
    }

    print("Cluster assignment to categories:", font_clusters)
    return kmeans, font_clusters


def categorize_text_based_on_clusters(text, metadata, kmeans, font_clusters):
    # Categorize a given text based on its font metadata using a trained k-means clustering model.

    if not font_clusters:
        raise ValueError("Font clusters are not initialized.")

    # Initialize a label encoder for encoding font names into numeric values
    le = LabelEncoder()

    # Transform font names from metadata into encoded values
    encoded_fonts = le.fit_transform([name for name, _ in metadata])

    # Calculate the average encoded font value
    avg_encoded_font = np.mean(encoded_fonts) if encoded_fonts.size > 0 else 0

    # Calculate the average font size
    avg_font_size = np.mean([size for _, size in metadata]) if metadata else 0

    # Predict the cluster of the given text based on its average font metadata
    cluster = kmeans.predict([[avg_encoded_font, avg_font_size]])[0]

    # Map the predicted cluster to its corresponding category
    category = next(
        (cat for cat, cluster_num in font_clusters.items() if cluster == cluster_num),
        "content",
    )

    print(f"[DEBUG] Predicted category: {category}")
    return {category: text}


def visualize_clusters(font_data, kmeans):
    print("[INFO] Visualizing clusters...")

    # Check if font_data is empty or None
    if not font_data:
        print("[WARNING] No font data points available. Skipping visualization.")
        return

    le = LabelEncoder()
    font_names = [item[0] for item in font_data]
    encoded_font_names = le.fit_transform(font_names).tolist()
    font_sizes = [item[1] for item in font_data]
    labels = list(kmeans.labels_)

    # Plot the clusters
    plt.scatter(encoded_font_names, font_sizes, c=labels, cmap="rainbow", alpha=0.5)

    # Plot the cluster centers
    centers = kmeans.cluster_centers_
    plt.scatter(
        centers[:, 0],
        centers[:, 1],
        c="black",
        s=200,
        marker="X",
        label="Cluster Center",
    )

    for i in range(0, len(font_names), 10):
        plt.annotate(
            font_names[i],
            (encoded_font_names[i], font_sizes[i]),
            textcoords="offset points",
            xytext=(0, 5),
            ha="center",
            fontsize=8,
            alpha=0.8,
        )
    print("Cluster Centers (Centroids):", kmeans.cluster_centers_)
    # Displaying axis labels and title
    plt.xlabel("Encoded Font Names")
    plt.ylabel("Font Sizes")
    plt.title("Visualization of clustered data")
    plt.colorbar(label="Cluster ID")
    plt.legend()
    print("[INFO] Close Visualization to continue...")
    plt.show(block=False)  # Display the plot without blocking the rest of the script.
    plt.pause(999999)  # Wait for X seconds.
    plt.close()
    print("[INFO] Visualization Done")


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
    return categorize_text_based_on_clusters(page_elements)


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
def process_page(page, pdfReader, pdf, pagenum, kmeans, font_clusters):
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
            categorized = categorize_text_based_on_clusters(
                line_text, format_per_line, kmeans, font_clusters
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


# Main script execution
def main():
    print("[INFO] Starting main execution...")

    # Open the specified PDF file in binary mode
    with open(PDF_PATH, "rb") as pdfFileObj:
        # Initialize a PDF reader object to manipulate the PDF
        pdfReader = PyPDF2.PdfReader(pdfFileObj)

        print("[DEBUG] Initializing PDF...")
        # Convert the PDF to a format suitable for further operations
        pdf = initialize_pdf(PDF_PATH)
        # Dictionary to hold the processed text data for each page
        text_per_page = {}

        print("[DEBUG] Gathering all font data...")
        # Extract font metadata from the entire PDF
        font_data = gather_all_font_data(PDF_PATH)

        print("[DEBUG] Initializing font clusters...")
        # Cluster the extracted font metadata using k-means clustering to categorize different text sections
        kmeans, font_clusters = initialize_font_clusters(font_data)

        print("[DEBUG] Visualizing clusters...")
        # Display a visualization of the font clusters for better understanding
        visualize_clusters(font_data, kmeans)

        # Iterate over each page of the PDF and process its content
        for pagenum, page in enumerate(extract_pages(PDF_PATH)):
            print(f"[DEBUG] Processing page number {pagenum + 1}...")
            # Extract and categorize content from each page
            page_content = process_page(
                page, pdfReader, pdf, pagenum, kmeans, font_clusters
            )

            # Update the dictionary with processed content for the current page
            text_per_page[f"Page_{pagenum}"] = page_content

        print("[DEBUG] Cleaning up temporary files...")
        # Remove temporary files generated during image extraction
        try:
            os.remove("cropped_image.pdf")
        except FileNotFoundError:
            pass

        try:
            os.remove("PDF_image.png")
        except FileNotFoundError:
            pass

        print("[DEBUG] Structuring processed PDF data...")
        # Organize the extracted content in a structured manner for easier consumption
        processed_data = structure_pdf_data(text_per_page)

        print("[DEBUG] Saving processed data to JSON...")
        # Convert the structured data to JSON format and save to disk
        save_data_to_json(processed_data)
        # Close the initialized PDF to free up resources
        pdf.close()

        print("[INFO] Completed!")


if __name__ == "__main__":
    main()
