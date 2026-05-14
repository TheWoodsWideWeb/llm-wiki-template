"""Tests for time filter (-t) on google-news and youtube-search."""

import unittest
from unittest.mock import patch, MagicMock


class TestGoogleNewsTimeFilter(unittest.TestCase):
    """Test that google-news passes tbs param correctly."""

    @patch("tools.google_news.requests.get")
    @patch("tools.google_news.get_env", return_value="fake-key")
    def test_no_time_filter(self, mock_env, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"news_results": []}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        from tools.google_news import search_google_news
        search_google_news("test query")

        _, kwargs = mock_get.call_args
        self.assertNotIn("tbs", kwargs["params"])

    @patch("tools.google_news.requests.get")
    @patch("tools.google_news.get_env", return_value="fake-key")
    def test_time_filter_day(self, mock_env, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"news_results": []}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        from tools.google_news import search_google_news
        search_google_news("test query", tbs="qdr:d")

        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["tbs"], "qdr:d")

    @patch("tools.google_news.requests.get")
    @patch("tools.google_news.get_env", return_value="fake-key")
    def test_time_filter_week(self, mock_env, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"news_results": []}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        from tools.google_news import search_google_news
        search_google_news("test query", tbs="qdr:w")

        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["tbs"], "qdr:w")


class TestGoogleNewsCLITimeFilter(unittest.TestCase):
    """Test CLI arg parsing converts shorthand to tbs."""

    def test_shorthand_conversion(self):
        """Verify -t d becomes qdr:d in argparse."""
        import sys
        from unittest.mock import patch as p

        # We test the main() arg parsing by checking it calls search_google_news correctly
        with p("tools.google_news.search_google_news") as mock_search, \
             p("tools.google_news.output_json"), \
             p("sys.argv", ["google-news", "test", "-t", "d"]):
            mock_search.return_value = {"query": "test", "news_results": [], "menu_links": []}
            from tools.google_news import main
            main()
            mock_search.assert_called_once_with(
                query="test", gl="us", hl="en", topic_token=None, tbs="qdr:d"
            )

    def test_shorthand_hour(self):
        with patch("tools.google_news.search_google_news") as mock_search, \
             patch("tools.google_news.output_json"), \
             patch("sys.argv", ["google-news", "test", "-t", "h"]):
            mock_search.return_value = {"query": "test", "news_results": [], "menu_links": []}
            from tools.google_news import main
            main()
            mock_search.assert_called_once_with(
                query="test", gl="us", hl="en", topic_token=None, tbs="qdr:h"
            )

    def test_raw_tbs_passthrough(self):
        with patch("tools.google_news.search_google_news") as mock_search, \
             patch("tools.google_news.output_json"), \
             patch("sys.argv", ["google-news", "test", "-t", "qdr:m"]):
            mock_search.return_value = {"query": "test", "news_results": [], "menu_links": []}
            from tools.google_news import main
            main()
            mock_search.assert_called_once_with(
                query="test", gl="us", hl="en", topic_token=None, tbs="qdr:m"
            )


class TestYouTubeSearchTimeFilter(unittest.TestCase):
    """Test that youtube-search passes sp param correctly."""

    @patch("tools.youtube_search.requests.get")
    @patch("tools.youtube_search.get_env", return_value="fake-key")
    def test_no_time_filter(self, mock_env, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"video_results": []}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        from tools.youtube_search import search_youtube
        search_youtube("test query")

        _, kwargs = mock_get.call_args
        self.assertNotIn("sp", kwargs["params"])

    @patch("tools.youtube_search.requests.get")
    @patch("tools.youtube_search.get_env", return_value="fake-key")
    def test_sp_passthrough(self, mock_env, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"video_results": []}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        from tools.youtube_search import search_youtube
        search_youtube("test query", sp="EgIIAg%3D%3D")

        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["sp"], "EgIIAg%3D%3D")


class TestYouTubeSearchCLITimeFilter(unittest.TestCase):
    """Test CLI arg parsing converts shorthand to sp."""

    def test_day_filter(self):
        with patch("tools.youtube_search.search_youtube") as mock_search, \
             patch("tools.youtube_search.output_json"), \
             patch("sys.argv", ["youtube-search", "test", "-t", "d"]):
            mock_search.return_value = {"query": "test", "video_results": [], "ads": [], "filters": []}
            from tools.youtube_search import main
            main()
            mock_search.assert_called_once_with(
                query="test", sp="EgIIAg%3D%3D", gl="us", hl="en"
            )

    def test_week_filter(self):
        with patch("tools.youtube_search.search_youtube") as mock_search, \
             patch("tools.youtube_search.output_json"), \
             patch("sys.argv", ["youtube-search", "test", "-t", "w"]):
            mock_search.return_value = {"query": "test", "video_results": [], "ads": [], "filters": []}
            from tools.youtube_search import main
            main()
            mock_search.assert_called_once_with(
                query="test", sp="EgIIAw%3D%3D", gl="us", hl="en"
            )

    def test_month_filter(self):
        with patch("tools.youtube_search.search_youtube") as mock_search, \
             patch("tools.youtube_search.output_json"), \
             patch("sys.argv", ["youtube-search", "test", "-t", "m"]):
            mock_search.return_value = {"query": "test", "video_results": [], "ads": [], "filters": []}
            from tools.youtube_search import main
            main()
            mock_search.assert_called_once_with(
                query="test", sp="EgIIBA%3D%3D", gl="us", hl="en"
            )

    def test_no_filter(self):
        with patch("tools.youtube_search.search_youtube") as mock_search, \
             patch("tools.youtube_search.output_json"), \
             patch("sys.argv", ["youtube-search", "test"]):
            mock_search.return_value = {"query": "test", "video_results": [], "ads": [], "filters": []}
            from tools.youtube_search import main
            main()
            mock_search.assert_called_once_with(
                query="test", sp=None, gl="us", hl="en"
            )


if __name__ == "__main__":
    unittest.main()
