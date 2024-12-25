from pydantic import BaseModel
from cat.mad_hatter.decorators import plugin

# settings
class ConfluenceDocsSettings(BaseModel):
    # String
    CONFLUENCE_SPACE_KEY: str
    # String
    CONFLUENCE_HOMEPAGE_ID: str = ""
    # String
    CONFLUENCE_URL: str
    # String
    CONFLUENCE_USERNAME: str
    # String
    CONFLUENCE_TOKEN: str
    # String
    PROMPT_CONTEXT: str = "Sei il Project Manager di un progetto che ha la knowledge-base su Confluence"

# Set settings to Cheshire
@plugin
def settings_model():
    return ConfluenceDocsSettings