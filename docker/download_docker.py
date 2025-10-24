"""
1. Before running this script, you should first check if you could access the docker hub api.
```curl -I https://hub.docker.com/v2/```
2. Check if you could login to the docker hub.
```docker login```
3. Docker access the docker hub api to check if the image exists.
```docker manifest inspect {image_name}```
4. If the image exists, you can pull the image.
```docker pull {image_name}```
"""

import os
import json
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download docker images for SWE-Dev dataset.")
    parser.add_argument('--split', choices=['train', 'test'], required=True, help='Which split to pull images for')
    args = parser.parse_args()

    # remote docker repository
    remote_docker_repo = "https://hub.docker.com/v2/repositories/"

    # Open docker_map.json
    with open("docker/docker_map.json", "r") as f:
        docker_map = json.load(f)

    split = args.split
    pkg_ls = docker_map[split]
    for pkg in pkg_ls:
        image_name = f"dorothyduuu/swe-dev:{pkg}-image"
        print(f"Checking {image_name} ...")
        ret = os.system(f"docker manifest inspect {image_name} > /dev/null 2>&1")
        if ret == 0:
            print(f"✅ {image_name} exists and can be pulled.")
            print(f"Pulling {image_name} ...")
            os.system(f"docker pull {image_name}")
        else:
            print(f"❌ {image_name} does NOT exist or cannot be pulled.")



