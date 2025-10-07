"""
Test suite for founder_finder.py
"""

import json
import os
import pytest
import tempfile
from unittest.mock import patch, AsyncMock
from founder_finder import parse_companies_file, find_founders
from claude_agent_sdk import AssistantMessage, TextBlock


class TestParseCompaniesFile:
    """Tests for parsing the companies.txt file"""

    def test_parse_valid_format(self):
        """Test parsing companies in 'Name (URL)' format"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Airbnb (https://www.airbnb.com/)\n")
            f.write("Dropbox (https://www.dropbox.com/)\n")
            temp_path = f.name

        try:
            companies = parse_companies_file(temp_path)
            assert len(companies) == 2
            assert companies[0] == {'name': 'Airbnb', 'url': 'https://www.airbnb.com/'}
            assert companies[1] == {'name': 'Dropbox', 'url': 'https://www.dropbox.com/'}
        finally:
            os.unlink(temp_path)

    def test_parse_empty_lines(self):
        """Test that empty lines are skipped"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Airbnb (https://www.airbnb.com/)\n")
            f.write("\n")
            f.write("Dropbox (https://www.dropbox.com/)\n")
            temp_path = f.name

        try:
            companies = parse_companies_file(temp_path)
            assert len(companies) == 2
        finally:
            os.unlink(temp_path)

    def test_parse_company_names_with_spaces(self):
        """Test parsing company names that contain spaces"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Read AI (https://www.read.ai/)\n")
            f.write("Wayfinder Bio (https://www.wayfinderbio.com/)\n")
            temp_path = f.name

        try:
            companies = parse_companies_file(temp_path)
            assert len(companies) == 2
            assert companies[0]['name'] == 'Read AI'
            assert companies[1]['name'] == 'Wayfinder Bio'
        finally:
            os.unlink(temp_path)

    def test_parse_fallback_no_url(self):
        """Test fallback when URL is missing"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Airbnb\n")
            temp_path = f.name

        try:
            companies = parse_companies_file(temp_path)
            assert len(companies) == 1
            assert companies[0] == {'name': 'Airbnb', 'url': ''}
        finally:
            os.unlink(temp_path)


class TestFindFounders:
    """Tests for the find_founders function"""

    @pytest.mark.asyncio
    async def test_find_founders_valid_response(self):
        """Test finding founders with XML final tag"""
        async def mock_query(*args, **kwargs):
            # Create mock objects that match the real SDK structure
            text_block = type('TextBlock', (), {'text': '<final>["Brian Chesky", "Joe Gebbia", "Nathan Blecharczyk"]</final>'})()
            message = type('AssistantMessage', (), {'content': [text_block]})()
            yield message

        with patch('founder_finder.query', side_effect=mock_query):
            with patch('founder_finder.AssistantMessage', return_value=type('AssistantMessage', (), {})):
                with patch('founder_finder.TextBlock', return_value=type('TextBlock', (), {})):
                    # Patch isinstance to work with our mocks
                    original_isinstance = __builtins__.isinstance
                    def mock_isinstance(obj, classinfo):
                        if classinfo.__name__ == 'AssistantMessage' and hasattr(obj, 'content'):
                            return True
                        if classinfo.__name__ == 'TextBlock' and hasattr(obj, 'text'):
                            return True
                        return original_isinstance(obj, classinfo)

                    with patch('builtins.isinstance', side_effect=mock_isinstance):
                        founders = await find_founders("Airbnb", "https://www.airbnb.com")
                        assert founders == ["Brian Chesky", "Joe Gebbia", "Nathan Blecharczyk"]

    @pytest.mark.asyncio
    async def test_find_founders_empty_result(self):
        """Test when no founders are found"""
        async def mock_query(*args, **kwargs):
            message = AssistantMessage(content=[
                TextBlock(text='[]')
            ])
            yield message

        with patch('founder_finder.query', side_effect=mock_query):
            founders = await find_founders("Unknown Company", "https://example.com")
            assert founders == []

    @pytest.mark.asyncio
    async def test_find_founders_with_markdown(self):
        """Test handling response wrapped in markdown code blocks"""
        async def mock_query(*args, **kwargs):
            message = AssistantMessage(content=[
                TextBlock(text='```json\n["John Doe", "Jane Smith"]\n```')
            ])
            yield message

        with patch('founder_finder.query', side_effect=mock_query):
            founders = await find_founders("Test Co", "https://test.com")
            assert founders == ["John Doe", "Jane Smith"]

    @pytest.mark.asyncio
    async def test_find_founders_invalid_json(self):
        """Test handling invalid JSON response"""
        async def mock_query(*args, **kwargs):
            message = AssistantMessage(content=[
                TextBlock(text='This is not JSON')
            ])
            yield message

        with patch('founder_finder.query', side_effect=mock_query):
            founders = await find_founders("Test Co", "https://test.com")
            assert founders == []

    @pytest.mark.asyncio
    async def test_find_founders_exception_handling(self):
        """Test exception handling during agent execution"""
        async def mock_query(*args, **kwargs):
            raise Exception("API Error")
            yield  # This won't be reached but makes it a generator

        with patch('founder_finder.query', side_effect=mock_query):
            founders = await find_founders("Test Co", "https://test.com")
            assert founders == []


class TestOutputFormat:
    """Tests for validating the output format"""

    def test_output_is_valid_json(self):
        """Test that a sample output file is valid JSON"""
        sample_output = {
            "Airbnb": ["Brian Chesky", "Joe Gebbia", "Nathan Blecharczyk"],
            "Dropbox": ["Drew Houston", "Arash Ferdowsi"],
            "Unknown Company": []
        }

        # Test JSON serialization/deserialization
        json_str = json.dumps(sample_output, indent=2)
        parsed = json.loads(json_str)

        assert parsed == sample_output
        assert isinstance(parsed["Airbnb"], list)
        assert isinstance(parsed["Unknown Company"], list)
        assert len(parsed["Unknown Company"]) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
