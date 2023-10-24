# Senior_Capstone_Fall_2023

Download the Bert model for training:

```bash
wget https://storage.googleapis.com/bert_models/2018_10_18/cased_L-12_H-768_A-12.zip
unzip cased_L-12_H-768_A-12.zip
cp cased_L-12_H-768_A-12 bert_model/model
```

Running the application with Docker:

```bash
docker compose up --build
```

PDF PARSER:

Install Python Dependencies:
Before running the application, make sure you've installed the required Python packages. If you haven't already, set up a virtual environment for better isolation:

```bash
python -m venv venv
source venv/bin/activate   # On Windows, use: venv\Scripts\activate
```

Next, install the required packages using the pdfparser_requirements.txt file:

```bash
pip install -r pdfparser_requirements.txt
```

Install Tesseract (Optical character recognition):
Follow the tutorial here: https://linuxhint.com/install-tesseract-windows/

Which has a link for the download at: https://github.com/UB-Mannheim/tesseract/wiki

This allows the PDF Parser to extract the text from the images using OCR technology

Current Status
Final Version still in production.
