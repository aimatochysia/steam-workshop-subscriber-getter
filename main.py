import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
GITHUB_TOKEN = os.getenv("_GITHUB_TOKEN")
GITHUB_REPO = os.getenv("_GITHUB_REPO")
BRANCH_NAME = os.getenv("_BRANCH_NAME")
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents"
url = os.getenv("_STEAM_WORKSHOP")
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


csv_filename = "subscriber_count.csv"
response = requests.get(f"{GITHUB_API_URL}/{csv_filename}", headers={"Authorization": f"token {GITHUB_TOKEN}"})
if response.status_code == 200:
    
    file_content = response.json()['content']
    decoded_content = requests.utils.unquote(file_content)
    df = pd.read_csv(pd.compat.StringIO(decoded_content))
else:
    
    df = pd.DataFrame()

current_id = url.split("id=")[-1]
if current_id in df.columns:
    empty_index = df[current_id].first_valid_index()
    if empty_index is not None:
        new_index = empty_index + 1
        df.at[new_index, current_id] = current_subscribers
    else:
        df.loc[len(df), current_id] = current_subscribers
else:
    df[current_id] = [current_subscribers]

csv_buffer = df.to_csv(index=False)
commit_message = "Update subscriber count"
upload_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{csv_filename}"


upload_response = requests.put(upload_url, headers={
    "Authorization": f"token {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}, json={
    "message": commit_message,
    "content": requests.utils.quote(csv_buffer.encode('utf-8').decode('utf-8')),
    "sha": response.json().get("sha") if response.status_code == 200 else None
})

if upload_response.status_code in (201, 200):
    print("CSV updated successfully.")
else:
    print("Failed to update the CSV on GitHub. Status code:", upload_response.status_code)
