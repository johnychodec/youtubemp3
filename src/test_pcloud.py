"""Test script for pCloud integration."""
import os
import logging
import tempfile
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from pcloud import PyCloud
from bot import YouTubeBot

# Configure logging first
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level='DEBUG'  # Set to DEBUG for more verbose output
)
logger = logging.getLogger(__name__)

# Get the project root directory (where .env should be)
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
logger.debug(f"Looking for .env at: {env_path}")

# Load environment variables
load_success = load_dotenv(env_path)
logger.debug(f"Load .env success: {load_success}")

# Debug: Print all environment variables (excluding actual values)
logger.debug("Environment variables present:")
for key in os.environ:
    if 'PCLOUD' in key:
        logger.debug(f"- {key}: {'*' * 8}")  # Don't print actual values

def get_folder_id(pcloud: PyCloud, folder_name: str, parent_id: int = 0) -> int:
    """Get folder ID by name and parent ID."""
    try:
        # List contents of parent folder
        folder_list = pcloud.listfolder(folderid=parent_id)
        
        # Look for our folder
        for item in folder_list['metadata']['contents']:
            if item['name'] == folder_name and item['isfolder']:
                return item['folderid']
        
        # If we get here, folder doesn't exist
        logger.debug(f"Creating new folder '{folder_name}' in parent {parent_id}")
        result = pcloud.createfolder(name=folder_name, folderid=parent_id)
        return result['metadata']['folderid']
    except Exception as e:
        logger.error(f"Error handling folder '{folder_name}': {e}")
        raise

def get_public_folder_id(pcloud: PyCloud) -> int:
    """Get the ID of the Public folder."""
    try:
        # List root folder contents
        root = pcloud.listfolder(folderid=0)
        
        # Look for Public folder
        for item in root['metadata']['contents']:
            if item['name'] == 'Public' and item['isfolder']:
                logger.info("Found Public folder")
                return item['folderid']
        
        raise Exception("Public folder not found in root directory")
    except Exception as e:
        logger.error(f"Error finding Public folder: {e}")
        raise

def test_pcloud_integration():
    try:
        # Initialize pCloud client
        username = os.getenv('PCLOUD_EMAIL')
        password = os.getenv('PCLOUD_PASSWORD')
        pcloud = PyCloud(username, password)

        # Test folder creation
        print("Testing folder creation...")
        folder_name = "test_folder"
        
        # Try to list the root folder first
        root_contents = pcloud.listfolder(folderid=0)
        logger.debug(f"Root folder contents: {root_contents}")
        
        # Look for existing test folder
        folder_id = None
        if isinstance(root_contents, dict) and 'metadata' in root_contents:
            for item in root_contents['metadata'].get('contents', []):
                if item.get('name') == folder_name and item.get('isfolder'):
                    folder_id = item.get('folderid')
                    print(f"Found existing folder with ID: {folder_id}")
                    break
        
        # Create folder if it doesn't exist
        if not folder_id:
            folder_info = pcloud.createfolder(name=folder_name, folderid=0)
            logger.debug(f"Folder creation response: {folder_info}")
            
            if not isinstance(folder_info, dict):
                raise Exception(f"Unexpected response type: {type(folder_info)}")
                
            if 'result' in folder_info and folder_info['result'] != 0:
                raise Exception(f"Failed to create folder: {folder_info.get('error', 'Unknown error')}")
                
            folder_id = folder_info.get('metadata', {}).get('folderid')
            if not folder_id:
                raise Exception("Could not get folder ID from response")
            
            print(f"Created new folder with ID: {folder_id}")

        # Create a test file
        print("Creating test file...")
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            temp_file.write("This is a test file for pCloud integration")
            temp_path = temp_file.name

        # Test file upload
        print("Testing file upload...")
        with open(temp_path, 'rb') as f:
            file_data = f.read()
            upload_result = pcloud.uploadfile(
                data=file_data,
                filename=os.path.basename(temp_path),
                folderid=folder_id
            )
            logger.debug(f"Upload result: {upload_result}")
            
            if not isinstance(upload_result, dict):
                raise Exception(f"Unexpected upload response type: {type(upload_result)}")
                
            if 'fileids' not in upload_result:
                raise Exception("No file IDs in upload response")
                
            file_id = upload_result['fileids'][0]
            print(f"✅ File uploaded successfully with ID: {file_id}")

        # Cleanup
        print("Cleaning up...")
        os.unlink(temp_path)
        pcloud.deletefile(fileid=file_id)
        pcloud.deletefolder(folderid=folder_id)
        print("Cleanup completed successfully")

        return True

    except Exception as e:
        logger.error(f"Error in test_pcloud_integration: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_pcloud_integration()
    if success:
        print("All pCloud integration tests passed successfully!")
    else:
        print("pCloud integration tests failed. Check the logs for details.")
        exit(1) 