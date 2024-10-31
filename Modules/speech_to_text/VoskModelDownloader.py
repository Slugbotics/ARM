import requests
import zipfile
import os
from tqdm import tqdm

def download_and_extract_vosk_model(url: str, output_dir: str) -> str:
    """
    Download and extract the Vosk model from the given URL.
    
    Args:
        url (str): The URL to the Vosk model zip file.
        output_dir (str): The directory where the model should be extracted.

    Returns:
        str: Path to the extracted model directory.
    """
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Extract the filename from the URL
    filename = os.path.join(output_dir, url.split("/")[-1])

    # Download the model with a progress bar
    response = requests.get(url, stream=True)
    total_size_in_bytes = int(response.headers.get('content-length', 0))
    block_size = 1024  # 1 Kilobyte
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)

    with open(filename, 'wb') as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
    progress_bar.close()

    # Check if the download was successful
    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        raise Exception("Error: Download failed")

    # Extract the zip file
    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall(output_dir)

    # Remove the zip file after extraction
    os.remove(filename)

    # Return the path to the extracted model directory
    extracted_dir = os.path.join(output_dir, zip_ref.namelist()[0])
    return extracted_dir

if __name__ == "__main__":
    # Example usage
    model_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"  # Replace with desired model URL
    output_directory = "./vosk_models"
    model_path = download_and_extract_vosk_model(model_url, output_directory)

    print(f"Model downloaded and extracted to: {model_path}")
