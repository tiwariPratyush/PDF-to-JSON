# PDF to JSON Parser

A Python utility that extracts and structures content from PDF files into organized JSON format. This tool intelligently parses text, tables, and images while maintaining document hierarchy and section structure.

## Features

- **Smart Content Classification**: Automatically identifies sections, subsections, and paragraphs based on font size, boldness, and word count
- **Table Extraction**: Uses Camelot to extract tables with lattice detection
- **Image Detection**: Identifies and catalogs charts/images within the document
- **Hierarchical Structure**: Maintains document organization with section and subsection tracking
- **Clean Text Processing**: Removes unwanted characters and normalizes whitespace
- **Command-line Interface**: Easy to use from terminal or scripts

## Installation

### Prerequisites

Make sure you have Python 3.7+ installed on your system.

### Dependencies

Install the required packages using pip:

```bash
pip install PyMuPDF camelot-py pandas numpy argparse
```

For Camelot to work properly, you may also need to install additional system dependencies:

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-tk ghostscript
```

**macOS:**
```bash
brew install ghostscript
```

**Windows:**
- Download and install Ghostscript from https://www.ghostscript.com/download/gsdnld.html

## Usage

### Command Line

```bash
python pdf_parser.py input_file.pdf output_file.json
```

### Example

```bash
python pdf_parser.py report.pdf structured_report.json
```

### Programmatic Usage

```python
from pdf_parser import parse_pdf_to_json
import json

# Parse PDF and get structured data
extracted_data = parse_pdf_to_json("document.pdf")

# Save to JSON file
with open("output.json", "w", encoding="utf-8") as f:
    json.dump(extracted_data, f, ensure_ascii=False, indent=4)
```

## Output Format

The parser generates a JSON structure with the following format:

```json
{
  "pages": [
    {
      "page_number": 1,
      "content": [
        {
          "type": "paragraph",
          "section": "Introduction",
          "sub_section": null,
          "text": "This is the introduction text..."
        },
        {
          "type": "table",
          "section": "Data Analysis",
          "sub_section": "Results",
          "description": null,
          "table_data": [
            ["Header1", "Header2", "Header3"],
            ["Row1Col1", "Row1Col2", "Row1Col3"],
            ["Row2Col1", "Row2Col2", "Row2Col3"]
          ]
        },
        {
          "type": "chart",
          "section": "Data Analysis",
          "sub_section": "Visualizations",
          "description": "Image/Chart 1 on page 1",
          "Table_data": null
        }
      ]
    }
  ]
}
```

## Content Types

The parser identifies and categorizes content into three main types:

### 1. Paragraphs
- Regular text content
- Automatically classified as sections, subsections, or paragraphs
- Maintains hierarchical context

### 2. Tables
- Extracted using Camelot's lattice detection
- Preserves table structure with headers and data rows
- Positioned correctly within document flow

### 3. Charts/Images
- Detected and cataloged with position information
- Includes descriptive placeholders
- Can be extended to include OCR or image analysis

## Configuration

The parser uses several configurable thresholds for content classification:

```python
# Font size thresholds for heading detection
HEADING_FONT_SIZE_THRESHOLD = 14.0
SUBHEADING_FONT_SIZE_THRESHOLD = 11.5

# Word count threshold for heading detection
HEADING_WORD_COUNT_THRESHOLD = 10
```

These can be adjusted in the code to better match your document styles.

## Classification Logic

The parser uses intelligent heuristics to classify content:

1. **Sections**: Large font size (>14pt) + bold formatting
2. **Subsections**: Medium font size (>11.5pt) + bold formatting OR bold text with <10 words
3. **Paragraphs**: All other text content

## Logging

The parser includes comprehensive logging to help track processing:

```
2023-XX-XX XX:XX:XX - INFO - Starting parsing for 'document.pdf'...
2023-XX-XX XX:XX:XX - INFO - Processing page 1...
2023-XX-XX XX:XX:XX - WARNING - Could not read tables from page 2: [error details]
2023-XX-XX XX:XX:XX - INFO - Successfully parsed and saved output to 'output.json'
```

## Error Handling

- **Table Extraction Failures**: Logs warnings but continues processing
- **Missing Dependencies**: Clear error messages for installation issues
- **Corrupted PDFs**: Graceful handling with informative error messages

## Limitations

- Table extraction works best with clearly defined table structures
- Font-based classification may need tuning for different document styles
- Complex layouts with overlapping elements may require manual adjustment
- Image content analysis is limited to detection and positioning

## Troubleshooting

### Common Issues

1. **Camelot Import Error**:
   - Ensure Ghostscript is installed
   - Try `pip install camelot-py[cv]` for computer vision dependencies

2. **Table Detection Issues**:
   - Some tables may require the 'stream' flavor instead of 'lattice'
   - Adjust table detection parameters in the code

3. **Font Classification Problems**:
   - Modify the threshold constants for your specific document type
   - Check font information using `span['font']` debugging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source. Please check the license file for details.

## Support

For issues and questions:
- Check the troubleshooting section
- Review the logs for detailed error information
- Open an issue with sample PDF and error details

---

**Note**: This parser is designed for structured documents. For complex layouts or specialized document types, additional customization may be required.