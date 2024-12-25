from atlassian import Confluence
import os, json


# Confluence settings class
class ConfluenceSettings:
    # constructor
    def __init__(self, dict1):
        self.__dict__.update(dict1)


# Confluence Service to interact with the Confluence API
class ConfluenceService:

    # Connector service to Confluence
    confluence: None | Confluence = None
    settings: None | ConfluenceSettings = None

    # Connect to Confluence and initialize the connector
    def connect(self, confluence_settings: None | ConfluenceSettings = None):
        if not confluence_settings:
            Exception("Confluence connector not initialized")

        self.confluence = Confluence(
            url=confluence_settings.CONFLUENCE_URL,
            username=confluence_settings.CONFLUENCE_USERNAME,
            password=confluence_settings.CONFLUENCE_TOKEN,
        )
        self.settings = confluence_settings

    def get_page_by_id(self, page_id: str | int):
        """
        Get a page from Confluence
        """
        page = self.confluence.get_page_by_id(page_id, expand="body.view")

        return page

    def get_pages(
        self, page_index: int = 0, page_size: int = 100, remove_children: bool = False
    ):
        """
        Get all pages from Confluence
        """
        pages = self.confluence.get_all_pages_from_space(
            self.settings.CONFLUENCE_SPACE_KEY,
            start=page_index,
            limit=page_size,
            content_type="page",
            expand="body.view,depth.root,container",
        )

        return pages

    def get_children_page(self, parent_id: str | int):
        """
        Get all children of a page
        """
        children = self.confluence.get_page_child_by_type(parent_id)

        return children

    def get_ancestors_pages(self, page_id: str | int):
        """
        Get all ancestors of a page
        """
        ancestors = self.confluence.get_page_ancestors(page_id)

        return ancestors

    def get_connector(self):
        """
        Get the Confluence connector to make custom requests
        """
        return self.confluence


def init_test() -> None:
    """
    Use this method to test the Confluence connector and make custom requests
    """
    settings = json.load(open(os.path.join(os.path.dirname(__file__), "settings.json")))
    print("Settings", settings)
    print()
    settings = json.loads(json.dumps(settings), object_hook=ConfluenceSettings)
    confluence_service = ConfluenceService()
    confluence_service.connect(settings)
    # custom request here


# init_test()
