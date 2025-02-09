from typing import Dict, List, Any
from prefect import flow, task
from .sparrow_client import SparrowClient
import configparser
import io
from pypdf import PdfReader
from pdf2image import convert_from_bytes
import logging


# Create a ConfigParser object
config = configparser.ConfigParser()

# Read the properties file
config.read("config.properties")

# Fetch settings
page_type_list = config.get("settings-medical-prescriptions", "page_type_to_process").split(',')
query_adjudication_table = config.get("settings-medical-prescriptions", "query_adjudication_table")
options_adjudication_table = config.get("settings-medical-prescriptions", "options_adjudication_table")
query_adjudication_details = config.get("settings-medical-prescriptions", "query_adjudication_details")
options_adjudication_details = config.get("settings-medical-prescriptions", "options_adjudication_details")
crop_size_adjudication_details = config.get("settings-medical-prescriptions", "crop_size_adjudication_details")


logger = logging.getLogger(__name__)


class DocumentError(Exception):
    """Custom exception for document processing errors"""
    pass


@task(name="detect_doc_structure")
async def detect_doc_structure(input_data: Dict[str, Any], sparrow_client: SparrowClient) -> Dict:
    """
    Detects document structure and validates PDF requirements.
    Only processes multi-page PDF documents.

    Args:
        input_data: Dictionary with file content and metadata
        sparrow_client: Instance of SparrowClient for API calls

    Returns:
        Dictionary with document structure information

    Raises:
        DocumentError: If document is not a valid multi-page PDF
    """
    content_type = input_data.get('content_type', '')
    filename = input_data.get('filename', '')

    is_pdf = content_type.lower() == 'application/pdf' or filename.lower().endswith('.pdf')
    if not is_pdf:
        raise DocumentError(f"Document must be PDF. Received: {content_type}")

    pdf_content = io.BytesIO(input_data['content'])
    pdf_reader = PdfReader(pdf_content)

    if len(pdf_reader.pages) <= 1:
        raise DocumentError("Document must contain multiple pages")

    return await sparrow_client.extract_type_per_page_sparrow(input_data)


@task(name="split_document")
async def split_document(input_data: Dict[str, Any], doc_structure: Dict) -> List[Dict]:
    """
    Splits document into pages and converts them to images.

    Args:
        input_data: Dictionary with file content
        doc_structure: Document structure from Sparrow API

    Returns:
        List of dictionaries containing page images and their types
    """
    page_types = {item['page']: item['page_type'] for item in doc_structure}

    images = convert_from_bytes(
        input_data['content'],
        dpi=300,
        fmt='png'
    )

    pages = []
    for page_num, image in enumerate(images, start=1):
        current_page_type = page_types.get(page_num)

        # Only process pages whose type is in the configured list
        if current_page_type not in page_type_list:
            logger.info(f"Skipping page {page_num} - type {current_page_type} not in configured types")
            continue

        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')

        pages.append({
            'content': img_byte_arr.getvalue(),
            'page_type': page_types[page_num]
        })

    return pages


@task(name="process_adjudication_table")
async def process_adjudication_table(page_data: Dict[str, Any], sparrow_client: SparrowClient) -> Dict:
    """
    Process pages of type 'adjudication_table' using Sparrow API.

    Args:
        page_data: Dictionary containing page content and metadata
        sparrow_client: Instance of SparrowClient for API calls

    Returns:
        Dictionary containing extracted data
    """
    try:
        # Specific parameters for adjudication table processing
        params = {
            "query": query_adjudication_table,
            "options": options_adjudication_table,
            "crop_size": ""
        }

        result = await sparrow_client.extract_data_sparrow(
            content=page_data['content'],
            params=params
        )

        return {
            'page_type': 'adjudication_table',
            'extracted_data': result,
            'status': 'success'
        }
    except Exception as e:
        logger.error(f"Error processing adjudication table: {str(e)}")
        return {
            'page_type': 'adjudication_table',
            'error': str(e),
            'status': 'failed'
        }


@task(name="process_adjudication_details")
async def process_adjudication_details(page_data: Dict[str, Any], sparrow_client: SparrowClient) -> Dict:
    """
    Process pages of type 'adjudication_details' using Sparrow API.

    Args:
        page_data: Dictionary containing page content and metadata
        sparrow_client: Instance of SparrowClient for API calls

    Returns:
        Dictionary containing extracted data
    """
    try:
        # Specific parameters for adjudication details processing
        params = {
            "query": query_adjudication_details,
            "options": options_adjudication_details,
            "crop_size": crop_size_adjudication_details
        }

        result = await sparrow_client.extract_data_sparrow(
            content=page_data['content'],
            params=params
        )

        return {
            'page_type': 'adjudication_details',
            'extracted_data': result,
            'status': 'success'
        }
    except Exception as e:
        logger.error(f"Error processing adjudication details: {str(e)}")
        return {
            'page_type': 'adjudication_details',
            'error': str(e),
            'status': 'failed'
        }


@task(name="extract_data")
async def extract_data(pages: List[Dict], sparrow_client: SparrowClient) -> List:
    """
        Extract data from document pages based on their type.

        Args:
            pages: List of dictionaries containing page content and type
            sparrow_client: Instance of SparrowClient for API calls

        Returns:
            List of dictionaries containing extracted data for each page
        """
    results = []

    for page in pages:
        page_type = page.get('page_type')

        if page_type == 'adjudication_table':
            result = await process_adjudication_table(page, sparrow_client)
        elif page_type == 'adjudication_details':
            result = await process_adjudication_details(page, sparrow_client)
        else:
            logger.warning(f"Unsupported page type: {page_type}")
            continue

        results.append(result)

    return results


class MedicalPrescriptionsAgent:
    """
    Agent for processing medical prescriptions using Sparrow API.
    """

    def __init__(self):
        self.name = "medical_prescriptions"
        self.capabilities = {"document_analysis", "data_extraction"}
        self.sparrow_client = SparrowClient()

    @flow(name="medical_prescriptions_flow")
    async def execute(self, input_data: Dict) -> Dict:
        """
        Main document processing flow
        """
        # Process and validate input
        doc_structure = await detect_doc_structure(input_data, self.sparrow_client)

        # Split document into pages
        pages = await split_document(input_data, doc_structure)

        # Process each page
        results = await extract_data(pages, self.sparrow_client)

        return {
            'filename': input_data['filename'],
            'total_pages_processed': len(pages),
            'results': results
        }