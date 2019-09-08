import os
import json
from datetime import datetime
from bs4 import BeautifulSoup

from blog import Post, GitMngr, meetup_to_markdown
from meetup import Meetup

# Import config
with open("config.json", "r") as config_file:
    raw_config = config_file.read()

config = json.loads(raw_config)

# Initialize git settings
git_mgr = GitMngr(github_user=config["github_user"], github_token=config["github_token"], github_repo=config["github_repo"])
git_mgr.update_master()
git_mgr.create_new_branch()

# Retrieve data
meetup_retriever = Meetup("GCPUGSG")
data = meetup_retriever.get_meetup_list()

changes_detected = False

for item in data:
    created_post_time = datetime.fromtimestamp(item['created']/1000)
    event_time = datetime.fromtimestamp(item["time"]/1000)
    content = meetup_to_markdown(item["description"])
    new_post = Post(item["name"], event_time, item["link"], created_post_time, content)
    
    filepath = os.path.join(os.curdir, 'gcpugsg', 'content', 'post', new_post.filename)
    previous_file_content = ''
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            previous_file_content = file.read()
    if previous_file_content != new_post.render():
        print("Expected output is not the same, re-create blog and save once more")
        with open(filepath, 'w+') as file:
            file.write(new_post.render())
        changes_detected = True
        
if changes_detected:
    print("Changes detected. Attempt to make PR to suggest changes")
    git_mgr.add_commit(os.path.join(".", 'content'))
    ok_to_create_PR = git_mgr.can_create_pr()
    if ok_to_create_PR:
        git_mgr.push_managed_branch()
        git_mgr.create_pull_request()
    else:
        print("Automated PR raised not yet merged. Please merge PR; this tool will raise any new PR till the initial merge is done")

git_mgr.checkout_branch("master")
git_mgr.delete_managed_branch()
