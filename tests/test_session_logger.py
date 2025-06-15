import pytest
from utils.session_logger import SessionLogger
import os
import tempfile

def test_log_session_header():
    with tempfile.TemporaryDirectory() as temp_dir:
        logger = SessionLogger(sessions_dir=temp_dir)
        logger.log_session_header("resume.txt", "job.txt", "resume content", "stories")
        logger.save()
        assert os.path.exists(logger.session_file)
        with open(logger.session_file, "r") as f:
            content = f.read()
            assert "resume.txt" in content
            assert "job.txt" in content
            assert "resume content" in content
            assert "stories" in content

def test_log_output():
    with tempfile.TemporaryDirectory() as temp_dir:
        logger = SessionLogger(sessions_dir=temp_dir)
        logger.log_output("output content")
        logger.save()
        with open(logger.session_file, "r") as f:
            content = f.read()
            assert "output content" in content

def test_log_story_prompt():
    with tempfile.TemporaryDirectory() as temp_dir:
        logger = SessionLogger(sessions_dir=temp_dir)
        logger.log_story_prompt("skill", "question")
        logger.save()
        with open(logger.session_file, "r") as f:
            content = f.read()
            assert "skill" in content
            assert "question" in content

def test_log_story_response():
    with tempfile.TemporaryDirectory() as temp_dir:
        logger = SessionLogger(sessions_dir=temp_dir)
        logger.log_story_response("skill", "question", "response")
        logger.save()
        with open(logger.session_file, "r") as f:
            content = f.read()
            assert "skill" in content
            assert "question" in content
            assert "response" in content

def test_log_story_already_answered():
    with tempfile.TemporaryDirectory() as temp_dir:
        logger = SessionLogger(sessions_dir=temp_dir)
        logger.log_story_already_answered("skill", "summary")
        logger.save()
        with open(logger.session_file, "r") as f:
            content = f.read()
            assert "skill" in content
            assert "summary" in content

def test_log_no_experience():
    with tempfile.TemporaryDirectory() as temp_dir:
        logger = SessionLogger(sessions_dir=temp_dir)
        logger.log_no_experience("skill", "question")
        logger.save()
        with open(logger.session_file, "r") as f:
            content = f.read()
            assert "skill" in content
            assert "question" in content

def test_save():
    with tempfile.TemporaryDirectory() as temp_dir:
        logger = SessionLogger(sessions_dir=temp_dir)
        logger.save()
        assert os.path.exists(logger.session_file)

def test_session_logger_init_with_session_file():
    logger = SessionLogger(session_file="custom_session.txt")
    assert logger.session_file == "custom_session.txt"
    assert logger.timestamp is None
    assert logger.entries == [] 