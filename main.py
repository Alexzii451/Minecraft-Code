import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time

def fetch_json_data(url):
    response = requests.get(url)
    return response.json()

def parse_claims_from_json(data):
    claims = []
    areas = data['sets']['me.angeschossen.lands']['areas']
    for claim_id, claim_data in areas.items():
        description_html = claim_data['desc']
        soup = BeautifulSoup(description_html, 'html.parser')

        # Extract the name
        name_element = soup.find('span')
        name = name_element.text.strip() if name_element else "Unknown"

        # Extract balance
        balance_str = "0"
        balance_element = soup.find(string=lambda x: 'Balance' in x)
        if balance_element:
            try:
                balance_str = balance_element.split(': ')[1].strip().replace(',', '').replace('$', '')
            except IndexError:
                print(f"Error parsing balance for claim {claim_id}: {balance_element}")

        # Extract chunks
        chunks_str = "0"
        chunks_element = soup.find(string=lambda x: 'Chunks' in x)
        if chunks_element:
            try:
                chunks_str = chunks_element.split(': ')[1].strip()
            except IndexError:
                print(f"Error parsing chunks for claim {claim_id}: {chunks_element}")

        # Extract players
        players_str = "Unknown"
        players_element = soup.find(string=lambda x: 'Players' in x)
        if players_element:
            try:
                players_str = players_element.split(': ')[1].strip()
            except IndexError:
                print(f"Error parsing players for claim {claim_id}: {players_element}")

        claim_info = {
            'id': claim_id,
            'name': name,
            'balance': float(balance_str),
            'chunks': int(chunks_str),
            'players': players_str,
            'coordinates': {
                'x': claim_data['x'],
                'z': claim_data['z']
            },
            'map_image_url': f"https://map.stoneworks.gg/tiles/_markers_/marker_world/{claim_id}.png"
        }
        claims.append(claim_info)

    return claims

def save_claims(claims, filename):
    with open(filename, 'w') as file:
        json.dump(claims, file, indent=4)

def load_claims(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    return []

def compare_claims(old_claims, new_claims):
    old_claims_dict = {claim['id']: claim for claim in old_claims}
    new_claims_dict = {claim['id']: claim for claim in new_claims}

    removed_claims = []
    added_claims = []

    for old_id, old_claim in old_claims_dict.items():
        if old_id not in new_claims_dict:
            # Check if this claim's coordinates match any new claim (name change detection)
            coordinates_match = False
            for new_claim in new_claims_dict.values():
                if old_claim['coordinates'] == new_claim['coordinates']:
                    coordinates_match = True
                    break
            if not coordinates_match:
                removed_claims.append(old_claim)

    for new_id, new_claim in new_claims_dict.items():
        if new_id not in old_claims_dict:
            added_claims.append(new_claim)

    return removed_claims, added_claims

def get_latest_log_files(log_folder):
    log_files = [f for f in os.listdir(log_folder) if f.endswith('.json')]
    log_files.sort(reverse=True)
    if len(log_files) < 2:
        return None, None
    return log_files[0], log_files[1]

def fetch_and_save_data():
    url = 'https://map.stoneworks.gg/tiles/_markers_/marker_world.json'
    data = fetch_json_data(url)
    claims = parse_claims_from_json(data)

    logs_dir = 'LandClaimsChecker/logs'
    removed_dir = 'LandClaimsChecker/removed_logs'
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(removed_dir, exist_ok=True)

    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{logs_dir}/claims_{current_time}.json'
    save_claims(claims, filename)
    print(f"Saved {len(claims)} claims to '{filename}'.")

    latest_log, previous_log = get_latest_log_files(logs_dir)
    if latest_log and previous_log:
        new_claims = load_claims(f'{logs_dir}/{latest_log}')
        old_claims = load_claims(f'{logs_dir}/{previous_log}')
        removed_claims, added_claims = compare_claims(old_claims, new_claims)

        print(f"Removed Claims: {len(removed_claims)}")
        print(f"Added Claims: {len(added_claims)}")

        removed_filename = f'{removed_dir}/removed_claims_{current_time}.json'
        save_claims(removed_claims, removed_filename)

        if removed_claims:
            print("Removed Claims Sample:", removed_claims[:1])
        if added_claims:
            print("Added Claims Sample:", added_claims[:1])
    else:
        print("Not enough log files to compare.")

    with open('LandClaimsChecker/logs/summary_log.txt', 'a') as log_file:
        log_file.write(f"{datetime.now()}: Run completed. Added Claims: {len(added_claims)}, Removed Claims: {len(removed_claims)}\n")

if __name__ == '__main__':
    while True:
        fetch_and_save_data()
        time.sleep(1500)  # Sleep for 25 minutes (1500 seconds)
