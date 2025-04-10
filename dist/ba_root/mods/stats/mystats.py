import setting
import _ba
import ba
import json
import os
import shutil
import threading
import datetime
from typing import List, Dict  # Add this import at the top
from shop import Shop

import urllib.request
from ba._activitytypes import *

damage_data = {}
icon = '\ue01f'
ranks = []
top3Name = []

our_settings = setting.get_settings_data()

base_path = os.path.join(_ba.env()['python_directory_user'], "stats" + os.sep)
statsfile = base_path + 'stats.json'
FIREBASE_KEY_PATH = os.path.join(base_path, "serviceAccountKey.json")

cached_stats = {}
statsDefault = {
    "pb-IF4VAk4a": {
        "rank": 65,
        "name": "A DEFAULT GUY",
        "scores": 0,
        "total_damage": 0.0,
        "kills": 0,
        "deaths": 0,
        "games": 18,
        "kd": 0.0,
        "avg_score": 0.0,
        "aid": "pb-IF4VAk4a",
        "last_seen": "2022-04-26 17:01:13.715014"
    }
}


seasonStartDate = None


def get_all_stats():
    global seasonStartDate
    if os.path.exists(statsfile):
        with open(statsfile, 'r', encoding='utf8') as f:
            try:
                jsonData = json.loads(f.read())
            except:
                f = open(statsfile+".backup", encoding='utf-8')
                jsonData = json.load(f)
            try:
                stats = jsonData["stats"]
                seasonStartDate = datetime.datetime.strptime(
                    jsonData["startDate"], "%d-%m-%Y")
                _ba.season_ends_in_days = our_settings["statsResetAfterDays"] - (
                    datetime.datetime.now() - seasonStartDate).days
                
                # Check if season needs to reset
                if (datetime.datetime.now() - seasonStartDate).days >= our_settings["statsResetAfterDays"]:
                    # Create a copy of current stats with end date for history
                    end_date = datetime.datetime.now().strftime("%d-%m-%Y")
                    history_stats = {
                        "startDate": jsonData["startDate"],
                        "endDate": end_date,
                        "stats": stats,
                        "top_players": get_top_players(3)  # Add top 3 players
                    }
                    
                    # Save to local history file
                    save_to_history(history_stats)
                    
                    # Push to Firebase
                    try:
                        import firebase_admin
                        from firebase_admin import firestore
                        
                        # Initialize Firebase if not already done
                        if not firebase_admin._apps:
                            cred = firebase_admin.credentials.Certificate(FIREBASE_KEY_PATH)
                            firebase_admin.initialize_app(cred)
                        
                        db = firestore.client()
                        
                        # Format document ID (convert start date from "dd-mm-yyyy" to "dd_mm_yyyy")
                        doc_id = jsonData["startDate"].replace("-", "_")
                        
                        # Add document to halloffame collection
                        db.collection("halloffame").document(doc_id).set(history_stats)
                        print(f"Successfully added season stats to Firebase with ID: {doc_id}")
                    except Exception as e:
                        print(f"Error pushing to Firebase: {e}")
                    
                    # Reset current season
                    backupStatsFile()
                    seasonStartDate = datetime.datetime.now()
                    return statsDefault
                
                # For current season, don't include end date
                return stats
            except OSError as e:
                print(e)
                return jsonData
    else:
        return {}

def get_top_players(count: int = 3) -> List[Dict]:
    """Get top players by score from current stats"""
    stats = get_cached_stats()  # You'll need to implement this or use existing stats
    sorted_entries = sorted(
        stats.values(),
        key=lambda x: x['scores'],
        reverse=True
    )[:count]
    
    # Format the top players data
    top_players = []
    for i, entry in enumerate(sorted_entries, 1):
        top_players.append({
            "name": entry.get("name", "Unknown"),
            "rank": i,
            "avg_score": entry.get("scores", 0) / max(1, entry.get("games", 1)),
            "games": entry.get("games", 0),
            "last_seen": entry.get("last_seen", "")
        })
    
    return top_players

def save_to_history(history_data):
    """Saves season data to history file with start and end dates"""
    history_file = os.path.join(os.path.dirname(statsfile), "season_history.json")
    
    # Load existing history if it exists
    history = []
    if os.path.exists(history_file):
        with open(history_file, 'r', encoding='utf8') as f:
            try:
                history = json.load(f)
                if not isinstance(history, list):
                    history = []  # Reset if corrupted
            except:
                history = []
    
    # Add new season data to history
    history.append(history_data)
    
    # Save updated history
    with open(history_file, 'w', encoding='utf8') as f:
        json.dump(history, f, indent=2)


def backupStatsFile():
    shutil.copy(statsfile, statsfile.replace(
        ".json", "") + str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + ".json")


def dump_stats(s: dict):
    global seasonStartDate
    if seasonStartDate == None:
        seasonStartDate = datetime.datetime.now()
    s = {"startDate": seasonStartDate.strftime("%d-%m-%Y"), "stats": s}
    if os.path.exists(statsfile):
        shutil.copyfile(statsfile, statsfile+".backup")
        with open(statsfile, 'w', encoding='utf8') as f:
            f.write(json.dumps(s, indent=4, ensure_ascii=False))
            f.close()
    else:
        print('Stats file not found!')


def get_stats_by_id(account_id: str):
    a = get_cached_stats()
    if account_id in a:
        return a[account_id]
    else:
        return None


def get_cached_stats():
    return cached_stats


def get_sorted_stats(stats):
    entries = [(a['scores'], a['kills'], a['deaths'], a['games'],
                a['name'], a['aid']) for a in stats.values()]
    # this gives us a list of kills/names sorted high-to-low
    entries.sort(key=lambda x: x[1] or 0, reverse=True)
    return entries


def refreshStats():
    global cached_stats
    # lastly, write a pretty html version.
    # our stats url could point at something like this...
    pStats = get_all_stats()
    cached_stats = pStats
    entries = get_sorted_stats(pStats)
    rank = 0
    toppersIDs = []
    _ranks = []
    for entry in entries:
        if True:
            rank += 1
            scores = str(entry[0])
            kills = str(entry[1])
            deaths = str(entry[2])
            games = str(entry[3])
            name = str(entry[4])
            aid = str(entry[5])
            if rank < 6:
                toppersIDs.append(aid)
            # The below kd and avg_score will not be added to website's html document, it will be only added in stats.json
            try:
                kd = str(float(kills) / float(deaths))
                kd_int = kd.split('.')[0]
                kd_dec = kd.split('.')[1]
                p_kd = kd_int + '.' + kd_dec[:3]
            except Exception:
                p_kd = "0"
            try:
                avg_score = str(float(scores) / float(games))
                avg_score_int = avg_score.split('.')[0]
                avg_score_dec = avg_score.split('.')[1]
                p_avg_score = avg_score_int + '.' + avg_score_dec[:3]
            except Exception:
                p_avg_score = "0"
            if damage_data and aid in damage_data:
                dmg = damage_data[aid]
                dmg = str(str(dmg).split('.')[
                          0] + '.' + str(dmg).split('.')[1][:3])
            else:
                dmg = 0

            _ranks.append(aid)

            pStats[str(aid)]["rank"] = int(rank)
            pStats[str(aid)]["scores"] = int(scores)
            # not working properly
            pStats[str(aid)]["total_damage"] += float(dmg)
            pStats[str(aid)]["games"] = int(games)
            pStats[str(aid)]["kills"] = int(kills)
            pStats[str(aid)]["deaths"] = int(deaths)
            pStats[str(aid)]["kd"] = float(p_kd)
            pStats[str(aid)]["avg_score"] = float(p_avg_score)

    global ranks
    ranks = _ranks

    dump_stats(pStats)
    updateTop3Names(toppersIDs[0:3])

    from playersData import pdata
    pdata.update_toppers(toppersIDs)


def update(score_set):
    """
    Given a Session's ScoreSet, tallies per-account kills
    and passes them to a background thread to process and
    store.
    """
    # look at score-set entries to tally per-account kills for this round

    account_kills = {}
    account_deaths = {}
    account_scores = {}

    for p_entry in score_set.get_records().values():
        account_id = p_entry.player.get_v1_account_id()
        if account_id is not None:
            account_kills.setdefault(account_id, 0)  # make sure exists
            account_kills[account_id] += p_entry.accum_kill_count
            account_deaths.setdefault(account_id, 0)  # make sure exists
            account_deaths[account_id] += p_entry.accum_killed_count
            account_scores.setdefault(account_id, 0)  # make sure exists
            account_scores[account_id] += p_entry.accumscore
    # Ok; now we've got a dict of account-ids and kills.
    # Now lets kick off a background thread to load existing scores
    # from disk, do display-string lookups for accounts that need them,
    # and write everything back to disk (along with a pretty html version)
    # We use a background thread so our server doesn't hitch while doing this.

    if account_scores:
        UpdateThread(account_kills, account_deaths, account_scores).start()

def get_client_id(account_id):
    for ros in ba.internal.get_game_roster():
        if ros["account_id"] == account_id:
            return ros["client_id"]
    return None

def display_the_tickets_earned(account_id,tickets_increment):
    cli_id = get_client_id(account_id)
    #print(cli_id)
    message = f"You have earned {tickets_increment} tickets {icon} in this match!"
    _ba.pushcall(lambda: _ba.screenmessage(message, color=(1, 1, 1), transient=True, clients=[cli_id]))

def update_tickets_in_bank(account_id, tickets_increment):
    ba.pushcall(lambda: display_the_tickets_earned(account_id, tickets_increment), from_other_thread=True)
    
    # Import shop's update function (circular imports may need handling)
    
    # Update the cache directly
    Shop.update_bank_cache(account_id, {'tickets': tickets_increment})
    
    
    print(f"{account_id} earned {tickets_increment} tickets")

def update_stats_cache_in_backend():
    global seasonStartDate
    """Send cached stats to the backend server"""
    try:
        import requests
        stats_data = get_cached_stats()
        
        if not stats_data:
            print("Warning: No stats data available to send")
            return

        url = our_settings['backendURLtoCacheStats']
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        json_data = {
            "data": {
                "startDate":seasonStartDate.strftime("%d-%m-%Y") if seasonStartDate else None,
                "stats": stats_data,
            }
        }

        print(f"Sending to {url} with data: {json.dumps(json_data, indent=2)}")  # Debug
        
        response = requests.post(
            url,
            json=json_data,
            headers=headers,
            timeout=5
        )
        
        response.raise_for_status()
        print(f"Success! Status: {response.status_code}, Response: {response.text}")
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print(f"Response content: {e.response.text}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

class UpdateThread(threading.Thread):
    def __init__(self, account_kills, account_deaths, account_scores):
        threading.Thread.__init__(self)
        self._account_kills = account_kills
        self.account_deaths = account_deaths
        self.account_scores = account_scores

    def run(self):
        # pull our existing stats from disk
        import datetime
        try:
            stats = get_all_stats()
        except:
            stats = {}

        # now add this batch of kills to our persistant stats
        for account_id, kill_count in self._account_kills.items():
            # add a new entry for any accounts that dont have one
            if account_id not in stats:
                # also lets ask the master-server for their account-display-str.
                # (we only do this when first creating the entry to save time,
                # though it may be smart to refresh it periodically since
                # it may change)
                stats[account_id] = {'rank': 0,
                                     'name': "deafult name",
                                     'scores': 0,
                                     'total_damage': 0,
                                     'kills': 0,
                                     'deaths': 0,
                                     'games': 0,
                                     'kd': 0,
                                     'avg_score': 0,
                                     'last_seen': str(datetime.datetime.now()),
                                     'aid': str(account_id)}
            # Temporary codes to change 'name_html' to 'name'
            # if 'name_html' in stats[account_id]:
            #     stats[account_id].pop('name_html')
            #     stats[account_id]['name'] = 'default'
            url = "http://bombsquadgame.com/bsAccountInfo?buildNumber=20258&accountID=" + account_id
            data = urllib.request.urlopen(url)
            if data is not None:
                try:
                    name = json.loads(data.read())["profileDisplayString"]
                except ValueError:
                    stats[account_id]['name'] = "???"
                else:
                    stats[account_id]['name'] = name

            # now increment their kills whether they were already there or not
            #print(stats[account_id])
            stats[account_id]['kills'] += kill_count
            stats[account_id]['deaths'] += self.account_deaths[account_id]
            stats[account_id]['scores'] += self.account_scores[account_id]
            stats[account_id]['last_seen'] = str(datetime.datetime.now())
            # also incrementing the games played and adding the id
            stats[account_id]['games'] += 1
            stats[account_id]['aid'] = str(account_id)
            # Increment tickets: 5 tickets for each kill =================================NANI=============================
            # Update tickets in bank.json for the corresponding account ID
            update_tickets_in_bank(account_id, kill_count * 5)

        # dump our stats back to disk
        tempppp = None
        from datetime import datetime
        dump_stats(stats)
        # aaand that's it!  There IS no step 27!
        now = datetime.now()
        update_time = now.strftime("%S:%M:%H - %d %b %y")
        # print(f"Added {str(len(self._account_kills))} account's stats entries. || {str(update_time)}")
        refreshStats()
            # Optional: Immediately save to disk or let it save later
        Shop.save_bank_data_to_disk()
        update_stats_cache_in_backend()


def getRank(acc_id):
    global ranks
    if ranks == []:
        refreshStats()
    if acc_id in ranks:
        return ranks.index(acc_id) + 1


def updateTop3Names(ids):
    global top3Name
    names = []
    for id in ids:
        url = "http://bombsquadgame.com/bsAccountInfo?buildNumber=20258&accountID=" + id
        data = urllib.request.urlopen(url)
        if data is not None:
            try:
                name = json.loads(data.read())["profileDisplayString"]
                if (not name):
                    raise ValueError
            except ValueError:
                names.append("???")
            else:
                names.append(name)
    top3Name = names
