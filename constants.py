"""Module providing API constants. ie.: urls"""

JIRA_STORIES_SEARCH = '/rest/api/3/search'

JIRA_VERSION_CREATE = '/rest/api/3/version'

JIRA_PROJECT_SEARCH = '/rest/api/3/project'

JIRA_ISSUE = 'rest/api/2/issue'

def jira_releases_search(project_key):
    return f"rest/api/3/project/{project_key}/version"