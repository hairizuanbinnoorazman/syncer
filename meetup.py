# File to handle meetup.com requests
import json
import requests

class Meetup:
    def __init__(self, meetup_group):
        self.BASE_ENDPOINT = "https://api.meetup.com"
        self.MEETUP_GROUP = meetup_group

    def get_meetup_list(self):
        url = "%s/%s/events" % (self.BASE_ENDPOINT, self.MEETUP_GROUP)
        resp = requests.get(url)
        data = json.loads(resp.content)
        return data


