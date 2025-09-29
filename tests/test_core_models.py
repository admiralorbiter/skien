# tests/test_core_models.py

import pytest
from datetime import datetime, date, timezone, timedelta
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from flask_app.models import (
    db, BaseModel, Story, EventClaim, Topic, Thread, Edge, EdgeRelation,
    Tag, EventStoryLink, StoryTag
)


@pytest.fixture
def test_topic(app):
    """Create a test topic fixture"""
    with app.app_context():
        topic = Topic(
            name='Test Topic',
            description='A test topic for testing',
            color='#FF0000'
        )
        db.session.add(topic)
        db.session.commit()
        return topic


@pytest.fixture
def test_story(app):
    """Create a test story fixture"""
    with app.app_context():
        story = Story(
            url='https://example.com/test-article',
            title='Test Article Title',
            source_name='Test Source',
            author='Test Author',
            published_at=date.today(),
            summary='This is a test article summary',
            raw_text='This is the full text of the test article.'
        )
        db.session.add(story)
        db.session.commit()
        return story


@pytest.fixture
def test_event(app, test_topic):
    """Create a test event fixture"""
    with app.app_context():
        event = EventClaim(
            topic_id=test_topic.id,
            claim_text='This is a test claim',
            event_date=date.today(),
            importance=3
        )
        db.session.add(event)
        db.session.commit()
        return event


@pytest.fixture
def test_thread(app, test_topic):
    """Create a test thread fixture"""
    with app.app_context():
        thread = Thread(
            topic_id=test_topic.id,
            name='Test Thread',
            description='A test thread for testing',
            start_date=date.today()
        )
        db.session.add(thread)
        db.session.commit()
        return thread


@pytest.fixture
def test_tag(app):
    """Create a test tag fixture"""
    with app.app_context():
        tag = Tag(name='test-tag')
        db.session.add(tag)
        db.session.commit()
        return tag


class TestBaseModel:
    """Test BaseModel functionality"""
    
    def test_base_model_creation(self, app):
        """Test that BaseModel provides common fields"""
        with app.app_context():
            # Create a simple model that inherits from BaseModel
            class TestModel(BaseModel):
                __tablename__ = 'test_models'
                name = db.Column(db.String(100), nullable=False)
            
            # Create table
            db.create_all()
            
            # Create instance
            test_obj = TestModel(name='test')
            db.session.add(test_obj)
            db.session.commit()
            
            assert test_obj.id is not None
            assert test_obj.created_at is not None
            assert test_obj.updated_at is not None
            assert test_obj.name == 'test'
    
    def test_to_dict(self, app):
        """Test to_dict method"""
        with app.app_context():
            class TestModel(BaseModel):
                __tablename__ = 'test_models2'
                name = db.Column(db.String(100), nullable=False)
            
            db.create_all()
            
            test_obj = TestModel(name='test')
            db.session.add(test_obj)
            db.session.commit()
            
            data = test_obj.to_dict()
            assert 'id' in data
            assert 'name' in data
            assert 'created_at' in data
            assert 'updated_at' in data
            assert data['name'] == 'test'
    
    def test_from_dict(self, app):
        """Test from_dict class method"""
        with app.app_context():
            class TestModel(BaseModel):
                __tablename__ = 'test_models3'
                name = db.Column(db.String(100), nullable=False)
            
            db.create_all()
            
            data = {'name': 'test_from_dict'}
            test_obj = TestModel.from_dict(data)
            
            assert test_obj.name == 'test_from_dict'
    
    def test_validate_required_fields(self, app):
        """Test validation of required fields"""
        with app.app_context():
            class TestModel(BaseModel):
                __tablename__ = 'test_models4'
                name = db.Column(db.String(100), nullable=False)
                optional_field = db.Column(db.String(100), nullable=True)
            
            db.create_all()
            
            # Test with missing required field
            test_obj = TestModel()
            errors = test_obj.validate()
            assert 'name is required' in errors
    
    def test_is_valid(self, app):
        """Test is_valid method"""
        with app.app_context():
            class TestModel(BaseModel):
                __tablename__ = 'test_models5'
                name = db.Column(db.String(100), nullable=False)
            
            db.create_all()
            
            # Test invalid object
            test_obj = TestModel()
            assert not test_obj.is_valid()
            
            # Test valid object
            test_obj.name = 'test'
            assert test_obj.is_valid()


class TestStoryModel:
    """Test Story model functionality"""
    
    def test_story_creation(self, test_story):
        """Test creating a story with all fields"""
        assert test_story.url == 'https://example.com/test-article'
        assert test_story.title == 'Test Article Title'
        assert test_story.source_name == 'Test Source'
        assert test_story.author == 'Test Author'
        assert test_story.published_at == date.today()
        assert test_story.summary == 'This is a test article summary'
        assert test_story.raw_text == 'This is the full text of the test article.'
    
    def test_story_validation(self, app):
        """Test story validation"""
        with app.app_context():
            # Test valid story
            story = Story(
                url='https://example.com/valid',
                title='Valid Title',
                source_name='Valid Source'
            )
            assert story.is_valid()
            
            # Test invalid URL
            story.url = 'not-a-url'
            errors = story.validate()
            assert 'URL format is invalid' in errors
    
    def test_canonicalize_url(self, app):
        """Test URL canonicalization"""
        with app.app_context():
            story = Story(
                url='https://example.com/article?utm_source=test&utm_medium=web&id=123',
                title='Test',
                source_name='Test Source'
            )
            story.canonicalize_url()
            assert story.url == 'https://example.com/article?id=123'
    
    def test_get_domain(self, app):
        """Test domain extraction"""
        with app.app_context():
            story = Story(
                url='https://example.com/article',
                title='Test',
                source_name='Test Source'
            )
            assert story.get_domain() == 'example.com'
    
    def test_find_by_url(self, test_story, app):
        """Test finding story by URL"""
        with app.app_context():
            found = Story.find_by_url('https://example.com/test-article')
            assert found is not None
            assert found.id == test_story.id
    
    def test_find_duplicates(self, test_story, app):
        """Test finding duplicate stories"""
        with app.app_context():
            # Create a similar story
            similar_story = Story(
                url='https://example.com/similar-article',
                title='Test Article Title',  # Same title
                source_name='Test Source',
                published_at=date.today()
            )
            db.session.add(similar_story)
            db.session.commit()
            
            duplicates = Story.find_duplicates(similar_story)
            assert len(duplicates) > 0
            assert any(dup['reason'] == 'title_similarity' for dup in duplicates)


class TestEventClaimModel:
    """Test EventClaim model functionality"""
    
    def test_event_creation(self, test_event, test_topic):
        """Test creating an event with all fields"""
        assert test_event.topic_id == test_topic.id
        assert test_event.claim_text == 'This is a test claim'
        assert test_event.event_date == date.today()
        assert test_event.importance == 3
    
    def test_event_validation(self, app, test_topic):
        """Test event validation"""
        with app.app_context():
            # Test valid event
            event = EventClaim(
                topic_id=test_topic.id,
                claim_text='Valid claim',
                event_date=date.today()
            )
            assert event.is_valid()
            
            # Test invalid importance
            event.importance = 10
            errors = event.validate()
            assert 'Importance must be between 1 and 5' in errors
    
    def test_get_all_stories(self, test_event, test_story, app):
        """Test getting all stories for an event"""
        with app.app_context():
            # Add story as primary
            test_event.story_primary_id = test_story.id
            db.session.commit()
            
            stories = test_event.get_all_stories()
            assert len(stories) == 1
            assert stories[0].id == test_story.id
    
    def test_can_connect_to(self, test_event, app, test_topic):
        """Test event connection validation"""
        with app.app_context():
            # Create another event in same topic
            other_event = EventClaim(
                topic_id=test_topic.id,
                claim_text='Other claim',
                event_date=date.today()
            )
            db.session.add(other_event)
            db.session.commit()
            
            can_connect, error = test_event.can_connect_to(other_event)
            assert can_connect
            assert error is None
            
            # Test self-connection
            can_connect, error = test_event.can_connect_to(test_event)
            assert not can_connect
            assert 'Cannot connect event to itself' in error


class TestTopicModel:
    """Test Topic model functionality"""
    
    def test_topic_creation(self, test_topic):
        """Test creating a topic with all fields"""
        assert test_topic.name == 'Test Topic'
        assert test_topic.description == 'A test topic for testing'
        assert test_topic.color == '#FF0000'
    
    def test_topic_validation(self, app):
        """Test topic validation"""
        with app.app_context():
            # Test valid topic
            topic = Topic(name='Valid Topic')
            assert topic.is_valid()
            
            # Test invalid color
            topic.color = 'not-a-color'
            errors = topic.validate()
            assert 'Color must be a valid hex color code' in errors
    
    def test_find_by_name(self, test_topic, app):
        """Test finding topic by name"""
        with app.app_context():
            found = Topic.find_by_name('Test Topic')
            assert found is not None
            assert found.id == test_topic.id
    
    def test_search_by_name(self, test_topic, app):
        """Test searching topics by name"""
        with app.app_context():
            results = Topic.search_by_name('Test')
            assert len(results) == 1
            assert results[0].id == test_topic.id


class TestThreadModel:
    """Test Thread model functionality"""
    
    def test_thread_creation(self, test_thread, test_topic):
        """Test creating a thread with all fields"""
        assert test_thread.topic_id == test_topic.id
        assert test_thread.name == 'Test Thread'
        assert test_thread.description == 'A test thread for testing'
        assert test_thread.start_date == date.today()
    
    def test_thread_validation(self, app, test_topic):
        """Test thread validation"""
        with app.app_context():
            # Test valid thread
            thread = Thread(
                topic_id=test_topic.id,
                name='Valid Thread'
            )
            assert thread.is_valid()
            
            # Test future date
            thread.start_date = date.today() + timedelta(days=1)
            errors = thread.validate()
            assert 'Start date cannot be in the future' in errors
    
    def test_add_event(self, test_thread, test_event, app):
        """Test adding event to thread"""
        with app.app_context():
            success, error = test_thread.add_event(test_event)
            assert success
            assert error is None
            assert test_event.thread_id == test_thread.id
    
    def test_find_by_topic(self, test_thread, test_topic, app):
        """Test finding threads by topic"""
        with app.app_context():
            threads = Thread.find_by_topic(test_topic.id)
            assert len(threads) == 1
            assert threads[0].id == test_thread.id


class TestEdgeModel:
    """Test Edge model functionality"""
    
    def test_edge_creation(self, test_event, app, test_topic):
        """Test creating an edge between events"""
        with app.app_context():
            # Create another event
            other_event = EventClaim(
                topic_id=test_topic.id,
                claim_text='Other claim',
                event_date=date.today()
            )
            db.session.add(other_event)
            db.session.commit()
            
            edge = Edge(
                src_event_id=test_event.id,
                dst_event_id=other_event.id,
                relation=EdgeRelation.FOLLOW_UP
            )
            db.session.add(edge)
            db.session.commit()
            
            assert edge.src_event_id == test_event.id
            assert edge.dst_event_id == other_event.id
            assert edge.relation == EdgeRelation.FOLLOW_UP
    
    def test_edge_validation(self, app):
        """Test edge validation"""
        with app.app_context():
            # Test self-loop
            edge = Edge(
                src_event_id=1,
                dst_event_id=1,
                relation=EdgeRelation.FOLLOW_UP
            )
            errors = edge.validate()
            assert 'Event cannot be related to itself' in errors
    
    def test_get_relation_description(self, app):
        """Test getting relation description"""
        with app.app_context():
            edge = Edge(
                src_event_id=1,
                dst_event_id=2,
                relation=EdgeRelation.FOLLOW_UP
            )
            description = edge.get_relation_description()
            assert 'B happens after A and references/extends A' in description


class TestTagModel:
    """Test Tag model functionality"""
    
    def test_tag_creation(self, test_tag):
        """Test creating a tag"""
        assert test_tag.name == 'test-tag'
    
    def test_tag_validation(self, app):
        """Test tag validation"""
        with app.app_context():
            # Test valid tag
            tag = Tag(name='valid-tag')
            assert tag.is_valid()
            
            # Test empty name
            tag.name = ''
            errors = tag.validate()
            assert 'Tag name cannot be empty' in errors
    
    def test_normalize_name(self, app):
        """Test tag name normalization"""
        with app.app_context():
            tag = Tag(name='  Test Tag  ')
            tag.normalize_name()
            assert tag.name == 'test_tag'
    
    def test_find_or_create(self, app):
        """Test find or create functionality"""
        with app.app_context():
            # Create new tag
            tag, error = Tag.find_or_create('new-tag')
            assert tag is not None
            assert error is None
            assert tag.name == 'new-tag'
            
            # Find existing tag
            existing_tag, error = Tag.find_or_create('new-tag')
            assert existing_tag is not None
            assert existing_tag.id == tag.id


class TestEventStoryLinkModel:
    """Test EventStoryLink model functionality"""
    
    def test_link_creation(self, test_event, test_story, app):
        """Test creating event-story link"""
        with app.app_context():
            link = EventStoryLink(
                event_id=test_event.id,
                story_id=test_story.id,
                note='Test link'
            )
            db.session.add(link)
            db.session.commit()
            
            assert link.event_id == test_event.id
            assert link.story_id == test_story.id
            assert link.note == 'Test link'
    
    def test_create_link(self, test_event, test_story, app):
        """Test create_link class method"""
        with app.app_context():
            link, error = EventStoryLink.create_link(test_event, test_story, 'Test note')
            assert link is not None
            assert error is None
            assert link.note == 'Test note'


class TestStoryTagModel:
    """Test StoryTag model functionality"""
    
    def test_link_creation(self, test_story, test_tag, app):
        """Test creating story-tag link"""
        with app.app_context():
            link = StoryTag(
                story_id=test_story.id,
                tag_id=test_tag.id
            )
            db.session.add(link)
            db.session.commit()
            
            assert link.story_id == test_story.id
            assert link.tag_id == test_tag.id
    
    def test_create_link(self, test_story, test_tag, app):
        """Test create_link class method"""
        with app.app_context():
            link, error = StoryTag.create_link(test_story, test_tag)
            assert link is not None
            assert error is None


class TestModelRelationships:
    """Test model relationships and cascading"""
    
    def test_topic_thread_relationship(self, test_topic, test_thread, app):
        """Test topic-thread relationship"""
        with app.app_context():
            # Test topic has thread
            threads = test_topic.threads.all()
            assert len(threads) == 1
            assert threads[0].id == test_thread.id
            
            # Test thread belongs to topic
            assert test_thread.topic.id == test_topic.id
    
    def test_thread_event_relationship(self, test_thread, test_event, app):
        """Test thread-event relationship"""
        with app.app_context():
            # Add event to thread
            test_event.thread_id = test_thread.id
            db.session.commit()
            
            # Test thread has event
            events = test_thread.events.all()
            assert len(events) == 1
            assert events[0].id == test_event.id
            
            # Test event belongs to thread
            assert test_event.thread.id == test_thread.id
    
    def test_story_tag_relationship(self, test_story, test_tag, app):
        """Test story-tag relationship"""
        with app.app_context():
            # Refresh the objects to ensure they're attached to the session
            db.session.refresh(test_story)
            db.session.refresh(test_tag)
            
            # Create link
            link = StoryTag(story_id=test_story.id, tag_id=test_tag.id)
            db.session.add(link)
            db.session.commit()
            
            # Test relationships through the link
            assert link.story.id == test_story.id
            assert link.tag.id == test_tag.id
            assert link.story.title == test_story.title
            assert link.tag.name == test_tag.name
