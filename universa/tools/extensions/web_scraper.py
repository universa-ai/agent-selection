import requests

from bs4 import BeautifulSoup

from ..tool import ToolRegistry


@ToolRegistry.register_tool
def scrap_webpage_content(url: str) -> str:
    """
    Retrieves the contents of a webpage and returns the title and text.

    Args:
        url (str): The URL of the webpage to scrape.

    Returns:
        str: The title and text of the webpage, separated by a newline.
    """
    webpage = requests.get(url).text

    soup = BeautifulSoup(webpage, "lxml")

    text = soup.get_text("")

    if soup.title:
        title = str(soup.title.string)
    else:
        title = ""

    return f"{title}\n\n{text}"
