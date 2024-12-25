from cat.mad_hatter.decorators import hook
from cat.log import log
from cat.looking_glass.prompts import MAIN_PROMPT_PREFIX
from .connector import ConfluenceSettings, ConfluenceService
from enum import Enum
import os, json


# Enum for valid commands to use during chat
class valid_commands(Enum):
    default: list = ["/confluence_docs"]
    all_pages: list = ["/confluence_docs/load_all_pages"]
    get_page: list = ["/confluence_docs/get_page", "page_id"]
    read_stored_pages: list = ["/confluence_docs/read_stored_pages"]
    read_stored_page: list = [
        "/confluence_docs/read_stored_page",
        "page_file_name.html",
    ]
    delete_stored_pages: list = ["/confluence_docs/delete_stored_pages"]


# Confluence connector service
confluence_service = confluence_settings = None

# Abolute path of "stored_pages" folder
stored_pages_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "stored_pages"
)


# Change prompt prefix if needed
@hook(priority=10)
def agent_prompt_prefix(prefix, cat):
    settings = cat.mad_hatter.get_plugin().load_settings()
    return (
        settings["PROMPT_CONTEXT"]
        if hasattr(settings, "PROMPT_CONTEXT")
        else MAIN_PROMPT_PREFIX
    )


# Use Fast Reply hook to manage user commands
@hook(priority=10)
def agent_fast_reply(fast_reply, cat) -> dict:
    # Get user message
    settings = cat.mad_hatter.get_plugin().load_settings()
    initialize_connector(settings)
    user_message = cat.working_memory["user_message_json"]["text"]
    imported_pages = []
    return_direct = False

    try:
        # import all pages
        if user_message.startswith(valid_commands.all_pages.value[0]):
            log.info("Loading all pages from Confluence")
            homepage = []
            if confluence_settings.CONFLUENCE_HOMEPAGE_ID:
                homepage = [get_page_data(confluence_settings.CONFLUENCE_HOMEPAGE_ID)]
            imported_pages = get_pages_data(homepage, True)

        # import single page by given id
        elif user_message.startswith(valid_commands.get_page.value[0]):
            page_id = user_message.split(" ")[1]
            log.info(f"Getting page {page_id} from Confluence")
            imported_pages.append(get_page_data(page_id))

        # read stored pages
        elif user_message.startswith(valid_commands.read_stored_pages.value[0]):
            log.info("Reading all stored pages")
            stored_files = read_stored_pages()
            stored_files_total = len(stored_files)
            for file in stored_files:
                cat.rabbit_hole.ingest_file(cat, file_path, 400, 100)

            if stored_files_total > 0:
                response = f"Stored pages read ({stored_files_total})"
            else:
                response = "No stored pages found"

            return_direct = True

        # read stored page by given page name
        elif user_message.startswith(valid_commands.read_stored_page.value[0]):
            page_name = user_message.split(" ")[1]
            file_path = os.path.join(stored_pages_path, page_name)
            stored_files = read_stored_pages()
            found = False
            for file in stored_files:
                if file_path in file:
                    cat.rabbit_hole.ingest_file(cat, file_path, 400, 100)
                    response = f"Stored page read: {page_name}"
                    found = True
                    break

            if not found:
                response = f"Stored page not found: {page_name}"

            return_direct = True

        # delete all stored pages
        elif user_message.startswith(valid_commands.delete_stored_pages.value[0]):
            log.info("Deleting all stored pages")
            delated_files_number = delete_stored_pages()
            response = f"Stored pages deleted ({delated_files_number})"
            return_direct = True

        # show help commands
        elif user_message.startswith(valid_commands.default.value[0]):
            return_direct = True
            response = "Confluence Docs plugin loaded - help commands: \n" + "\n".join(
                [
                    str(
                        command.value[0]
                        + (" " + command.value[1] if len(command.value) > 1 else "")
                    )
                    for command in valid_commands
                ]
            )

        # import processor to store pages and memorize them
        if imported_pages:
            imported_pages = import_processor(imported_pages, cat)
            imported_pages = [
                str(page["title"] + ": " + page["file_path"] + "\n")
                for page in imported_pages
            ]
            return_direct = True
            response = f"Imported {len(imported_pages)} pages from Confluence: {''.join(imported_pages)}"

    except Exception as e:
        return_direct = True
        response = "Error loading pages from Confluence: " + str(e)

    # Manage response
    if return_direct:
        fast_reply["output"] = response

    return fast_reply


def initialize_connector(settings: dict) -> None:
    global confluence_service, confluence_settings
    # upscale dict settings to object settings
    confluence_settings = json.loads(
        json.dumps(settings), object_hook=ConfluenceSettings
    )
    confluence_service = ConfluenceService()
    confluence_service.connect(confluence_settings)


def import_processor(imported_pages: list, cat) -> dict:
    """Process imported pages"""
    for imported_page in imported_pages:
        storage_page_file_path = storage_page(imported_page)
        imported_page["file_path"] = storage_page_file_path
        if storage_page_file_path:
            cat.rabbit_hole.ingest_file(cat, storage_page_file_path, 400, 100)

    return imported_pages


def get_pages_data(pages: list = [], load_page: bool = False) -> list:
    global confluence_service
    """Get pages data from a list of Confluence pages"""
    results = []
    # use sent pages list and return data
    if pages:
        log.info("Getting pages data from Confluence by list")
        for page in pages:
            if load_page:
                page = get_page_data(page["id"])
            else:
                page = get_page_data(page["id"], page)

            if page:
                results.append(page)
                children = confluence_service.get_children_page(page["id"])
                if children:
                    results.extend(get_pages_data(children, True))

        return results

    log.info("Getting all pages data from Confluence")
    # iterate over all pages
    # init paginator
    page_index = 0
    page_limit = 100
    while True:
        pages = confluence_service.get_pages(page_index, page_limit, True)
        if not pages:
            break
        for page in pages:
            page = get_page_data(page["id"], page)
            if page:
                results.append(page)

        # move on paginator
        page_index = page_limit + 1
        page_limit += 100

    log.info(f"Imported pages: {len(results)}")
    return results


def get_page_data(page_id: str | int, page: dict = {}) -> dict:
    global confluence_service
    """Return data from Confluence page"""
    store_data = {}

    if not page or "body" not in page.keys():
        page = confluence_service.get_page_by_id(page_id)

    parent_id = None
    page_anchestors = confluence_service.get_ancestors_pages(page_id)
    if page_anchestors:
        parent_id = [
            f"{ancestor['id']}--{ancestor['title']}" for ancestor in page_anchestors
        ]

    if page:
        store_data = {
            "id": page["id"],
            "parent_id": parent_id,
            "title": page["title"],
            "content": page["body"]["view"]["value"],
            "base_url": f"{confluence_settings.CONFLUENCE_URL}/pages/viewpage.action?pageId={page['id']}",
            "url": f"{confluence_settings.CONFLUENCE_URL}/{page['_links']['webui']}",
        }

    return store_data


def storage_page(page_data: dict) -> str | None:
    """Stora page information in a file. Page data expected should be a dict with title, content, base_url and url"""
    page = f"""
    <html>
        <head>
            <title>{page_data['title']}</title>
        </head>
        <body>
            <h1>{page_data['title']}</h1>
            <p>Page URL: <a href="{page_data['url']}">{page_data['url']}</a></p>
            <p>Base URL: <a href="{page_data['base_url']}">{page_data['base_url']}</a></p>
            <p>Parent Page(s): {(", ".join(page_data['parent_id']) if page_data['parent_id'] else "")}</p>
            {page_data['content']}
        </body>
    </html>
    """
    file_name = f"{page_data['id']}--{page_data['title']}.html"
    file_dir = stored_pages_path
    if page_data["parent_id"]:
        for parent in page_data["parent_id"]:
            file_dir = os.path.join(file_dir, parent)
            os.makedirs(file_dir, exist_ok=True)

    file_path = os.path.join(file_dir, file_name)

    with open(file_path, "w") as file:
        log.info(f"Storing page: {page_data['title']} in {file_path}")
        file.write(page)
        return file_path

    return None


def read_stored_pages(dir: str | None = None) -> list:
    """Read all stored pages"""
    stored_pages = []
    if not dir:
        dir = stored_pages_path

    for file in os.listdir(dir):
        file_path = os.path.join(dir, file)
        if os.path.isfile(file_path) and file_path.endswith(".html"):
            with open(file_path, "r") as file:
                stored_pages.append(file.read())
        elif os.path.isdir(file_path):
            stored_pages.append(read_stored_pages(file_path))

    return stored_pages


def delete_stored_pages(dir: str | None = None) -> int:
    """Delete all stored pages"""
    removed = 0
    if not dir:
        dir = stored_pages_path

    for file in os.listdir(dir):
        file_path = os.path.join(dir, file)
        if os.path.isfile(file_path) and file_path.endswith(".html"):
            os.remove(file_path)
            removed += 1
        elif os.path.isdir(file_path):
            total_file = delete_stored_pages(file_path)
            os.removedirs(file_path)
            removed += total_file + 1

    return removed
