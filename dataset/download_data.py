# python dataset/download_data.py --dest ./data

import os
import argparse
from huggingface_hub import snapshot_download
import shutil


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", type=str, default="./data")
    return parser.parse_args()

def download_data(dest):
    temp_dir = "./temp_download"
    
    # Download to temporary directory
    snapshot_download(
        repo_id="Dorothydu/SWE-Dev",
        repo_type="dataset",
        revision="main",
        local_dir=temp_dir,
        ignore_patterns=["README.md", "*.md", ".gitattributes", "dataset_infos.json"]
    )
    
    # Create target directory
    os.makedirs(dest, exist_ok=True)
    
    # Only move data files (skip README, etc.)
    shutil.copytree(temp_dir+'/dataset', dest, dirs_exist_ok=True)
    
    # Clean up temporary directory
    shutil.rmtree(temp_dir)
    print(f"Downloaded dataset files to: {dest}")



if __name__ == "__main__":
    args = parse_args()
    download_data(args.dest)
    