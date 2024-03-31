from datetime import datetime
import requests
import os
import json
import re

BOOK_SERIES_DATA_URL = "https://github.com/Dimbreath/StarRailData/raw/master/ExcelOutput/BookSeriesConfig.json"
BOOK_SERIES_WORLD_URL = "https://github.com/Dimbreath/StarRailData/raw/master/ExcelOutput/BookSeriesWorld.json"
LOCALBOOK_DATA_URL = "https://github.com/Dimbreath/StarRailData/raw/master/ExcelOutput/LocalbookConfig.json"
TEXT_DATA_URL = "https://raw.githubusercontent.com/Dimbreath/StarRailData/master/TextMap/TextMapEN.json"

CLEANR = re.compile('<.*?>')


def clean(s: str):
    return re.sub(CLEANR, '', s)


# Returns True if it downloaded, False otherwise.
def download(force=False):
    if not force and os.path.exists("temp_output/book_processed_data.json"):
        last_modified = os.path.getmtime("temp_output/book_processed_data.json")
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
    with open("dl/dimbreath_book_series_data.json", 'wb') as db_bs_data_file:
        db_bs_data_file.write(requests.get(BOOK_SERIES_DATA_URL).content)
    with open("dl/dimbreath_book_series_world.json", 'wb') as db_bs_world_file:
        db_bs_world_file.write(requests.get(BOOK_SERIES_WORLD_URL).content)
    with open("dl/dimbreath_localbook_data.json", 'wb') as db_localbook_data_file:
        db_localbook_data_file.write(requests.get(LOCALBOOK_DATA_URL).content)
    with open("dl/dimbreath_textmap_EN.json", 'wb') as db_textmap_file:
        db_textmap_file.write(requests.get(TEXT_DATA_URL).content)
    print("Done downloading files.")
    return True


def process():
    with open("dl/dimbreath_book_series_data.json", 'r', encoding='utf-8') as db_bs_data_file:
        db_bs_data = json.load(db_bs_data_file)
    with open("dl/dimbreath_book_series_world.json", 'r', encoding='utf-8') as db_bs_world_file:
        db_bs_world = json.load(db_bs_world_file)
    with open("dl/dimbreath_localbook_data.json", 'r', encoding='utf-8') as db_localbook_data_file:
        db_localbook = json.load(db_localbook_data_file)
    with open("dl/dimbreath_textmap_EN.json", 'r', encoding='utf-8') as db_textmap_file:
        db_textmap = json.load(db_textmap_file)

    data = {}
    for bsw in db_bs_world.values():
        world: str = str(bsw["BookSeriesWorld"])
        world_name_hash: int = bsw["BookSeriesWorldTextmapID"]["Hash"]
        world_name: str = clean(db_textmap[str(world_name_hash)])
        print("Found world:", world, "name:", world_name)
        data[world] = {"WorldName": world_name, "Series": {}}

    for bs in db_bs_data.values():
        if "IsShowInBookshelf" not in bs or not bs["IsShowInBookshelf"]:
            continue
        bs_id: str = str(bs["BookSeriesID"])
        bs_world: str = str(bs["BookSeriesWorld"])
        bs_name_hash: int = bs["BookSeries"]["Hash"]
        bs_name: str = clean(db_textmap[str(bs_name_hash)])
        print("Found book series in world", bs_world, "with id:", bs_id, "\tname:", bs_name)
        data[bs_world]["Series"][bs_id] = {"Title": bs_name, "Books": {}}

    for book in db_localbook.values():
        b_id: str = str(book["BookID"])
        bs_id: str = str(book["BookSeriesID"])
        bs_index: int = book["BookSeriesInsideID"]
        b_name_hash: int = book["BookInsideName"]["Hash"]
        b_name: str = clean(db_textmap[str(b_name_hash)])
        print("Found book in book series", bs_id, "with id:", b_id, "at index", bs_index, "\tname:", b_name)
        world = str(db_bs_data[bs_id]["BookSeriesWorld"])
        if bs_id not in data[world]["Series"]:
            continue  # Meaning it doesn't show up in bookshelf
        data[world]["Series"][bs_id]["Books"][bs_index] = {"id": b_id, "title": b_name}

    if not os.path.exists("temp_output"):
        os.makedirs("temp_output")
    with open('temp_output/book_processed_data.json', 'w', encoding='utf-8') as proc_data_file:
        json.dump(data, proc_data_file, indent=4, ensure_ascii=False)


download(force=False)
process()
