import pytest
import os
import tempfile
import json
from utils.story_manager import StoryManager

def test_save_and_get_all_stories():
    with tempfile.TemporaryDirectory() as temp_dir:
        stories_file = os.path.join(temp_dir, "stories.json")
        manager = StoryManager(stories_file=stories_file)
        manager.save_story("Python", "Wrote a script.", True)
        manager.save_story("Leadership", "Led a team.", False)
        all_stories = manager.get_all_stories()
        assert len(all_stories) == 2
        assert all_stories[0]["skill"] == "Python"
        assert all_stories[1]["skill"] == "Leadership"

def test_get_relevant_stories():
    with tempfile.TemporaryDirectory() as temp_dir:
        stories_file = os.path.join(temp_dir, "stories.json")
        manager = StoryManager(stories_file=stories_file)
        manager.save_story("Python", "Wrote a script.", True)
        manager.save_story("Leadership", "Led a team.", False)
        relevant = manager.get_relevant_stories()
        assert len(relevant) == 1
        assert relevant[0]["skill"] == "Python"

def test_empty_stories_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        stories_file = os.path.join(temp_dir, "stories.json")
        manager = StoryManager(stories_file=stories_file)
        all_stories = manager.get_all_stories()
        assert all_stories == []
        relevant = manager.get_relevant_stories()
        assert relevant == []

def test_malformed_json():
    with tempfile.TemporaryDirectory() as temp_dir:
        stories_file = os.path.join(temp_dir, "stories.json")
        with open(stories_file, "w") as f:
            f.write("not a json")
        manager = StoryManager(stories_file=stories_file)
        all_stories = manager.get_all_stories()
        assert all_stories == []
        relevant = manager.get_relevant_stories()
        assert relevant == []

def test_save_story_appends():
    with tempfile.TemporaryDirectory() as temp_dir:
        stories_file = os.path.join(temp_dir, "stories.json")
        manager = StoryManager(stories_file=stories_file)
        manager.save_story("Skill1", "Story1", True)
        manager.save_story("Skill2", "Story2", True)
        with open(stories_file, "r") as f:
            data = json.load(f)
        assert len(data["stories"]) == 2
        assert data["stories"][0]["skill"] == "Skill1"
        assert data["stories"][1]["skill"] == "Skill2" 