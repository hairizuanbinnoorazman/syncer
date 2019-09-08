# File to handle gcpug blog
import re
import os
import json
import requests
import datetime
import subprocess
from bs4 import BeautifulSoup, NavigableString
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
    loader=FileSystemLoader(os.curdir),
    autoescape=select_autoescape(['html', 'xml'])
)

def meetup_to_markdown(content):
    content = content.replace("<br/>", "\n")
    soup = BeautifulSoup(content, features="html.parser")
    markdown = ""
    for element in soup:
        if isinstance(element, NavigableString):
            continue
        markdown = markdown + element.text + "\n\n"
    return markdown

class Post:
    def __init__(self, event_name, event_date, event_link, post_date, content):
        assert isinstance(event_name, str), "Expected string for title"
        assert isinstance(post_date, datetime.date), "Expected date for post_date"
        assert isinstance(content, str), "Expected string for content"
        assert isinstance(event_link, str), "Exepected string for event_link"
        assert isinstance(event_date, datetime.date), "Exepected string for event_link"
        self.event_name = event_name
        self.event_date = event_date
        self.event_link = event_link
        self.post_date = post_date
        self.content = content
        self.blog_directory = os.path.join(os.curdir, "gcpugsg/content/post")
        self.filename = "%s_%s.md" % (post_date.strftime("%Y%m%d"), re.sub(r"[^a-zA-Z0-9]+", ' ', event_name.strip().lower()).replace(" ", "-"))

    def render(self):
        template = env.get_template("template.md.j2")
        output = template.render(
            post_date=self.post_date.strftime("%Y-%m-%d"),
            post_title=self.event_name,
            event_date=self.event_date.strftime("%Y-%m-%d"), 
            event_link=self.event_link,
            content=self.content)
        return output


class GitMngr:
    def __init__(self, home_dir="", github_user="", github_token="", github_repo=""):
        self.home_dir = home_dir
        if home_dir == "":
            self.home_dir = os.path.join(os.curdir, "gcpugsg")
        self.default_branch = "master"
        self.managed_branch = ""
        self.github_user = github_user
        self.github_token = github_token
        self.github_repo = github_repo

    def can_create_pr(self):
        assert self.github_token != "", "No github password available"
        assert self.github_user != "", "No github user available"
        assert self.github_repo != "", "No github repo is available"
        url = "https://api.github.com/repos/%s/%s/pulls" % (self.github_user, self.github_repo)
        resp = requests.get(url, auth=(self.github_user, self.github_token))
        if resp.status_code != 200:
            return False
        data = json.loads(resp.content)
        for item in data:
            if "auto" in item["title"]:
                return False
        return True

    def create_pull_request(self):
        assert self.github_token != "", "No github password available"
        assert self.github_user != "", "No github user available"
        assert self.github_repo != "", "No github repo is available"
        assert self.managed_branch != "", "No managed branch is provided"
        url = "https://api.github.com/repos/%s/%s/pulls" % (self.github_user, self.github_repo)
        body = {
            "title": self.managed_branch,
            "head": self.managed_branch,
            "base": "master",
            "body": "This is an automatic PR raised from attempting to sync content between meetup.com and website"
        }
        resp = requests.post(url, json=body, auth=(self.github_user, self.github_token))
        if resp.status_code != 201:
            print(resp.status_code)
            print(resp.content)
            raise Exception("Unable to create Pull Request")

    def checkout_branch(self, branch_name):
        subprocess.call("cd %s && git checkout %s" % (self.home_dir, branch_name), shell=True)

    def create_new_branch(self, branch_name = ""):
        if branch_name == "" and self.managed_branch == "":
            branch_name = "auto_%s" % datetime.datetime.now().strftime("%Y%m%d_%H%M")
            self.managed_branch = branch_name
        else:
            raise Exception("Branch error")
        subprocess.call("cd %s && git checkout -b %s" % (self.home_dir, self.managed_branch), shell=True)

    def delete_managed_branch(self):
        if self.managed_branch == "":
            raise Exception("Not managing any branch now")
        subprocess.call("cd %s && git branch -D %s" % (self.home_dir, self.managed_branch), shell=True)
        self.managed_branch = ""

    def push_managed_branch(self):
        if self.managed_branch == "":
            raise Exception("Not managing any branch now")
        subprocess.call("cd %s && git push origin %s" % (self.home_dir, self.managed_branch), shell=True)

    def update_master(self):
        self.checkout_branch("master")
        subprocess.call("cd %s && git pull origin master" % (self.home_dir), shell=True)

    def add_commit(self, file_name):
        message = "Automated sync done on " + datetime.datetime.now().strftime("%Y%m%d %H%M")
        subprocess.call("cd %s && git add %s" % (self.home_dir, file_name), shell=True)
        subprocess.call("cd %s && git commit -m '%s'" % (self.home_dir, message), shell=True)

