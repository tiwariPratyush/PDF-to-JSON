import fitz  # PyMuPDF
import camelot
import json
import pandas as pd
import numpy as np
import argparse
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration for Content Classification ---
# These thresholds might need tuning for different document styles.
# A larger font size is more likely to be a header.
HEADING_FONT_SIZE_THRESHOLD = 14.0
SUBHEADING_FONT_SIZE_THRESHOLD = 11.5
# A text block with very few words is likely a title or heading.
HEADING_WORD_COUNT_THRESHOLD = 10

def is_bold(span):
    """Check if a text span is bold."""
    return "bold" in span['font'].lower()

def classify_text_block(block):
    """
    Classifies a text block as a 'section', 'sub_section', or 'paragraph'.
    Uses heuristics based on font size, boldness, and word count.
    """
    if not block['lines']:
        return "paragraph"  # Default for empty blocks

    # Get properties of the first line's first span for classification
    first_line = block['lines'][0]
    first_span = first_line['spans'][0]
    font_size = first_span['size']
    text = "".join([s['text'] for s in first_line['spans']]).strip()
    word_count = len(text.split())

    # Heuristic 1: Based on font size and boldness
    if font_size > HEADING_FONT_SIZE_THRESHOLD and is_bold(first_span):
        return "section"
    if font_size > SUBHEADING_FONT_SIZE_THRESHOLD and is_bold(first_span):
        return "sub_section"
    
    # Heuristic 2: Short, bold text is likely a heading
    if is_bold(first_span) and word_count < HEADING_WORD_COUNT_THRESHOLD:
        return "sub_section"

    return "paragraph"

def extract_tables_from_page(pdf_path, page_num):
    """Extracts tables from a specific page using Camelot."""
    try:
        tables = camelot.read_pdf(pdf_path, pages=str(page_num), flavor='lattice')
        return [table.df for table in tables]
    except Exception as e:
        logging.warning(f"Could not read tables from page {page_num}: {e}")
        return []

def clean_text(text):
    """Cleans extracted text by removing unwanted characters and lines."""
    # Remove excessive newlines and spaces
    text = re.sub(r'\s*\n\s*', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_pdf_to_json(pdf_path):
    """
    Main function to parse a PDF and structure its content into JSON.
    Iterates through pages and processes text, tables, and images.
    """
    doc = fitz.open(pdf_path)
    output_json = {"pages": []}
    
    # Extract tables for all pages at once for efficiency
    all_tables = {}
    for i in range(1, len(doc) + 1):
        all_tables[i] = extract_tables_from_page(pdf_path, i)

    current_section = None
    current_sub_section = None

    for page_num, page in enumerate(doc, 1):
        logging.info(f"Processing page {page_num}...")
        page_content = []
        
        # Get all elements sorted by their vertical position
        elements = page.get_text("dict")['blocks']
        
        # Add table placeholders to be sorted with text blocks
        page_tables = all_tables.get(page_num, [])
        for i, df in enumerate(page_tables):
            # Find the y-coordinate of the table to sort it correctly
            # This is an approximation using the text around the table area
            table_areas = camelot.read_pdf(pdf_path, pages=str(page_num), flavor='lattice')[i]._bbox
            elements.append({
                'type': 'table_placeholder',
                'bbox': (table_areas[0], table_areas[1], table_areas[2], table_areas[3]),
                'table_data': df,
                'table_index': i
            })
            
        # Add image placeholders
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            bbox = page.get_image_bbox(img)
            elements.append({
                'type': 'chart_placeholder',
                'bbox': bbox,
                'description': f"Image/Chart {img_index + 1} on page {page_num}"
            })

        # Sort all elements by their top (y0) coordinate
        elements.sort(key=lambda el: el['bbox'][1])

        for element in elements:
            if element.get('type') == 'table_placeholder':
                table_df = element['table_data']
                table_json = {
                    "type": "table",
                    "section": current_section,
                    "sub_section": current_sub_section,
                    "description": None, # Description can be manually added or inferred
                    "table_data": [table_df.columns.values.tolist()] + table_df.values.tolist()
                }
                page_content.append(table_json)
                continue

            if element.get('type') == 'chart_placeholder':
                chart_json = {
                    "type": "chart",
                    "section": current_section,
                    "sub_section": current_sub_section,
                    "description": element['description'],
                    "Table_data": None # Placeholder for data if found nearby
                }
                page_content.append(chart_json)
                continue

            # Process text blocks
            if 'lines' not in element:
                continue

            block_text = " ".join([
                span['text'] for line in element['lines'] for span in line['spans']
            ])
            block_text = clean_text(block_text)

            if not block_text:
                continue

            block_type = classify_text_block(element)

            if block_type == "section":
                current_section = block_text
                current_sub_section = None # Reset subsection on new section
            elif block_type == "sub_section":
                current_sub_section = block_text
            
            # We add all text blocks as paragraphs, but update the state
            # for subsequent elements.
            content_item = {
                "type": "paragraph",
                "section": current_section,
                "sub_section": current_sub_section,
                "text": block_text
            }
            page_content.append(content_item)

        output_json["pages"].append({
            "page_number": page_num,
            "content": page_content
        })
    
    doc.close()
    return output_json


def main():
    """Command-line interface for the PDF parser."""
    parser = argparse.ArgumentParser(description="Parse a PDF file and extract its content to a structured JSON file.")
    parser.add_argument("input_pdf", help="Path to the input PDF file.")
    parser.add_argument("output_json", help="Path to the output JSON file.")
    args = parser.parse_args()

    logging.info(f"Starting parsing for '{args.input_pdf}'...")
    
    extracted_data = parse_pdf_to_json(args.input_pdf)
    
    with open(args.output_json, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, ensure_ascii=False, indent=4)
        
    logging.info(f"Successfully parsed and saved output to '{args.output_json}'")


if __name__ == "__main__":
    main()