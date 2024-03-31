import re
from datetime import datetime
import requests
import os
import json

ACHIEVEMENT_DATA_URL = "https://github.com/Dimbreath/StarRailData/raw/master/ExcelOutput/AchievementData.json"
TEXT_DATA_URL = "https://raw.githubusercontent.com/Dimbreath/StarRailData/master/TextMap/TextMapEN.json"

CLEANR = re.compile('<.*?>')


def clean(s: str):
    return re.sub(CLEANR, '', s)

# Returns True if it downloaded, False otherwise.
def download(force=False):
    if not force and os.path.exists("temp_output/achievement_processed_data.json"):
        last_modified = os.path.getmtime("temp_output/achievement_processed_data.json")
        URL = "https://api.github.com/repos/Dimbreath/StarRailData/commits/master"
        PARAMS = {'Accept': 'application/vnd.github+json'}
        print("Checking last commit time...")
        commit = requests.get(url=URL, params=PARAMS).json()
        commit_date = datetime.strptime(commit["commit"]["committer"]["date"], "%Y-%m-%dT%H:%M:%SZ").timestamp()
        if last_modified > commit_date:
            print("Files are more recent than last commit, not downloading them.")
            return False
    print("Files either don't exist or are older than the last commit.")
    print("Downloading files...")
    if not os.path.exists("dl"):
        os.makedirs("dl")
    with open("dl/dimbreath_achievement_data.json", 'wb') as db_data_file:
        db_data_file.write(requests.get(ACHIEVEMENT_DATA_URL).content)
    with open("dl/dimbreath_textmap_EN.json", 'wb') as db_textmap_file:
        db_textmap_file.write(requests.get(TEXT_DATA_URL).content)
    print("Done downloading files.")
    return True


def process():
    with open('dl/dimbreath_achievement_data.json', 'r') as db_data_file:
        db_data = json.load(db_data_file)
    with open('dl/dimbreath_textmap_EN.json', 'r', encoding='utf-8') as db_textmap_file:
        db_textmap = json.load(db_textmap_file)

    data = {}
    for achievement in db_data.values():
        a_id = achievement["AchievementID"]
        text_hash = achievement["AchievementTitle"]["Hash"]
        title = clean(db_textmap[str(text_hash)])
        desc_hash = achievement["AchievementDesc"]["Hash"]
        desc = clean(db_textmap[str(desc_hash)])
        print("Found achievement:", a_id, "\twith text hash", text_hash, "\ttitle:", title)
        data[a_id] = {"title": title, "desc": desc}

    if not os.path.exists("temp_output"):
        os.makedirs("temp_output")
    with open('temp_output/achievement_processed_data.json', 'w', encoding='utf-8') as proc_data_file:
        json.dump(data, proc_data_file, indent=4, ensure_ascii=False)


download(force=False)
process()
