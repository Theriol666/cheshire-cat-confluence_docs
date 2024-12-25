# Statement
This is an experimental plugin to use Cheshire Cat as a RAG for Confluence documentation.

There are probably some features missing at the moment, but this plugin could be easily implemented via the files "confluence_docs.py" (to handle the logic in Cheshire Cat) and "connector.py" (to handle the connection with Confluence API).

This plugin has been tested on WSL2 with Python 3.10 and Core CCat v0.0.2. It requires the "atlassian-python-api" library (https://atlassian-python-api.readthedocs.io/) to work.

# Installation
Copy the "confluence_docs" folder inside the "plugin" folder.

Now go to the Cheshire Cat admin panel and go to the "Plugins" tab to enable "Atlassian Confluence Docs".

Once enabled, remember to configure the plugin before using it.

## Plugin Configuration
* Confluence Space Key: The key to your Confluence workspace
* Confluence Homepage Id: The ID of a specific page that groups the documentation (not required)
* Confluence URL: The URL of your workspace (for example: https://your-company.atlassian.net)
* Confluence Username: The username of your API user
* Confluence Token: The API token created by your API user (https://id.atlassian.com/manage-profile/security/api-tokens)
* Prompt Context: The main prompt used by Cheshire Cat to generate responses (not required but pre-populated)

# Commands
This plugin works before the Cheshire Cat's response.

Commands are:
* /confluence_docs : to show all commands
* /confluence_docs/load_all_pages : downloads all Confluence pages and stores a copy in plugins/confluence_docs/stored_pages as HTML; then sends everything to Cheshire Cat memory
* /confluence_docs/get_page [page_id] : downloads a Confluence page and stores it in plugins/confluence_docs/stored_pages as HTML; then sends it to Cheshire Cat memory
* /confluence_docs/read_stored_pages : sends all stored files to Cheshire Cat memory
* /confluence_docs/read_stored_page [file--name.html] : sends a specific stored file to Cheshire Cat memory
* /confluence_docs/delete_stored_pages : deletes all files stored in plugins/confluence_docs/stored_pages

Note: If you send the same page to Cheshire multiple times, it will be read as a new file, so the old information will remain.