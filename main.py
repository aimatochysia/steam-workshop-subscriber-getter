import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from git import Repo
import tempfile

load_dotenv()
GITHUB_TOKEN = os.getenv("_GITHUB_TOKEN")
GITHUB_REPO = os.getenv("_GITHUB_REPO")
BRANCH_NAME = os.getenv("_BRANCH_NAME")
url = os.getenv("_STEAM_WORKSHOP")

if url is None:
    print("Error: _STEAM_WORKSHOP is not set in the environment.")
    exit()

response = requests.get(url)
if response.status_code == 200:
    soup = BeautifulSoup(response.content, 'html.parser')
    tr_elements = soup.find_all('tr')
    current_subscribers = None
    for tr in tr_elements:
        td_elements = tr.find_all('td')
        if len(td_elements) == 2 and "Current Subscribers" in td_elements[1].text:
            current_subscribers = td_elements[0].text.strip().replace(',', '')
            break
else:
    print("Failed to retrieve the webpage. Status code:", response.status_code)
    exit()

TEMP_DIR = tempfile.mkdtemp()
Repo.clone_from(f'https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git', TEMP_DIR, branch=BRANCH_NAME)
csv_filename = os.path.join(TEMP_DIR, "subscriber_count.csv")

if os.path.exists(csv_filename) and os.path.getsize(csv_filename) > 0:
    df = pd.read_csv(csv_filename)
else:
    df = pd.DataFrame()

current_id = url.split("id=")[-1]

if current_id in df.columns:
    new_index = df[current_id].last_valid_index() + 1 if df[current_id].last_valid_index() is not None else 0
    df.at[new_index, current_id] = current_subscribers
else:
    df[current_id] = [current_subscribers]

df.to_csv(csv_filename, index=False)

repo = Repo(TEMP_DIR)
repo.git.add(csv_filename)
repo.index.commit("Update subscriber count")
repo.git.push("origin", BRANCH_NAME)

print("CSV updated and pushed successfully.")
