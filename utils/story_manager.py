import os
import json
from datetime import datetime

class StoryManager:
    def __init__(self, stories_file='resources/stories/stories.json'):
        self.stories_file = stories_file
        os.makedirs(os.path.dirname(self.stories_file), exist_ok=True)

    def load_stories(self):
        if os.path.exists(self.stories_file):
            with open(self.stories_file, 'r') as sf:
                try:
                    stories_data = json.load(sf)
                except Exception:
                    stories_data = {"stories": []}
        else:
            stories_data = {"stories": []}
        return stories_data

    def save_story(self, skill, story, has_experience=True):
        stories_data = self.load_stories()
        stories_data["stories"].append({
            "skill": skill,
            "story": story,
            "has_experience": has_experience,
            "timestamp": datetime.now().isoformat()
        })
        with open(self.stories_file, 'w') as sf:
            json.dump(stories_data, sf, indent=2)

    def get_relevant_stories(self):
        stories_data = self.load_stories()
        return [s for s in stories_data.get("stories", []) if s.get("has_experience")]

    def get_all_stories(self):
        stories_data = self.load_stories()
        return stories_data.get("stories", []) 