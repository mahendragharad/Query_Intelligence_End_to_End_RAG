import trafilatura
from src.loaders.base_loder import DocumentBaseLoader

class WebLoaderService(DocumentBaseLoader):
    """Web content loader for URL-based sources."""

    def __init__(self, url: str):
        self.url = str(url)

    def load(self) -> str:
        downloaded = trafilatura.fetch_url(self.url)
        if downloaded is None:
            raise ValueError("Unable to download the webpage.")

        article_text = trafilatura.extract(downloaded)
        if article_text is None:
            raise ValueError("Unable to extract article content from the page.")

        return article_text

    

