#!/usr/bin/env python3

import argparse
from operator import truediv
from urllib import response
import requests
import constants
import random
import json

TIMEOUT = 100

def config_cli_parser():
    ''' Configure Command Line Interface '''
    parser = argparse.ArgumentParser(description = "A text file manager!")

    parser.add_argument("-rv", "--releaseVersion", type = str,
                        metavar = "1.1.2", default = None,
                        help = "sets the release semantic version.")
     
    parser.add_argument("-au", "--atlassianUser", type = str, required=True,
                        metavar = "johndoe@company.com", default = None,
                        help = "sets the Atlassian user")
     
    parser.add_argument("-ap", "--atlassianPassword", type = str, required=True,
                        metavar = "password/api_key", default = None,
                        help = "sets the Atlassian user password or API key.")

    parser.add_argument("-jp", "--jiraProject", type = str, required=True,
                        metavar = "Jira Project Key", default = None,
                        help = "sets the Jira Project Key")
     
    parser.add_argument("-rnf", "--releaseNoteCustomField", type = str, required=True,
                        metavar = '10001', help = "Release Notes Jira Custom Field Number")
     
    parser.add_argument("-cs", "--confluenceSpaceName", type = str, required=True,
                        metavar = 'TEST',
                        help = "Confluence space name key where release note will be created")

    parser.add_argument("-ca", "--confluencePageAncestor", type = str, required=True,
                        metavar = '132221',
                        help = "Confluence parent page ID where release note will be created")

    parser.add_argument("-jAPI", "--jiraAPI", type = str, required=True,
                        metavar = 'https://jira.api/rest/',
                        help = "Jira Rest API base URL")

    parser.add_argument("-cAPI", "--confluenceAPI", type = str, required=True,
                        metavar = 'https://confluence.api/rest/',
                        help = "Confluence Rest API base URL")

    return parser

def get_completed_stories(jira_api_base_url, project_key, credentials):
    ''' Fetch the list of completed stories from the Next Release for a given project key '''
    search_stories_url = f"{jira_api_base_url}/{constants.JIRA_STORIES_SEARCH}"
    search_stories_url_params = {
        'jql': f"project='{project_key}' and fixVersion='Next-Release' and Status='Done'",
        'startAt': 0,
        'maxResults': 50
    }

    all_stories = []

    while True:
        stories = requests.get(search_stories_url, params=search_stories_url_params, auth=credentials, timeout=TIMEOUT)
        stories_json = stories.json()

        if not stories_json['issues']:
            break

        all_stories.extend(stories_json['issues'])
        search_stories_url_params['startAt'] += search_stories_url_params['maxResults']

    return all_stories

def get_completed_stories(jira_api_base_url, project_key, credentials):
    ''' Fetch the list of completed stories from the Next Release for a given project key '''
    search_stories_url = f"{jira_api_base_url}/{constants.JIRA_STORIES_SEARCH}"
    search_stories_url_params = {'jql': f"project=\"{project_key}\" and fixVersion=\"Next-Release\" and Status=\"Done\""}

    stories = requests.get(search_stories_url, params = search_stories_url_params, auth= credentials, timeout=TIMEOUT)

    return stories.json()

def create_release_notes(stories, jira_base_url, release_note_field_no):
    ''' Create Release Notes table '''
    html = "<div>"

    html += '<ul>'
    for story in stories['issues']:
        story_no = story['key']
        release_note = story['fields'][release_note_field_no]

        list_item = f"<li><a href='{jira_base_url}/browse/{story_no}' target='_blank'>{story_no}</a> {release_note}</li>"
        html += list_item

    html += '</ul></div>'
    return html

def get_random_release_fun_quote():
    ''' Get a witty release header '''
    quote = random.randrange(0,1)
    if quote == 0:
        headline = "Holy cow! The release is out!"
        headline_gif = "https://cdn.dribbble.com/users/49272/screenshots/3577612/media/1b8c974de4380c6ff55b9625179abffc.gif"
    elif quote == 1:
        headline = "Release is out! We fixed a few hairy bugs."
        headline_gif = "https://c.tenor.com/0ub-F8PevlwAAAAd/cow-lucioushair.gif"

    return f"<p style='margin: 0 50%; width: 100%;'>{headline}</p><img style='margin:0 50%' width='20%' height='20%' src='{headline_gif}'/>"

def get_release_id(jira_api_base_url, release_version, project_key, credentials):
    get_releases_url = f"{jira_api_base_url}/{constants.jira_releases_search(project_key)}"

    releases = requests.get(get_releases_url, auth= credentials, timeout=TIMEOUT)

    releases_json = releases.json()

    for release in releases_json["values"]:
        if release_version == release["name"]:
            return release["id"]
    
    return None

def get_html_payload(page_title, project_key, parent_page_id, html):
    return {
        'type': 'page',
        'title': page_title,
        'space' : {
            'key' : f"{project_key}"
        },
        'ancestors' : [{
            'id' : f"{parent_page_id}"
        }],
        'body' : {
            'storage': {
                'value' : f"{html}",
                'representation' : 'storage'
            }
        }
    }

def post_release_notes_content(html, confluence_url, credentials, release_version, project_key, parent_page_id):
    ''' Create or update release notes on Confluence '''
    page_title = f"Release - {release_version}"
    data = {
        'type': 'page',
        'title': page_title,
        'space' : {
            'key' : f"{project_key}"
        },
        'ancestors' : [{
            'id' : f"{parent_page_id}"
        }],
        'body' : {
            'storage': {
                'value' : f"{html}",
                'representation' : 'storage'
            }
        }
    }

    # Check if the page already exists
    search_url = f"{confluence_url}/rest/api/content"
    search_params = {
        'type': 'page',
        'title': page_title,
        'spaceKey': project_key,
        'limit': 1
    }
    search_response = requests.get(search_url, params=search_params, auth=credentials, timeout=TIMEOUT)

    if search_response.status_code == 200:
        search_results = search_response.json()['results']
        if search_results:
            # Page already exists, update it
            page_id = search_results[0]['id']
            page_hist = requests.get(f"{confluence_url}/rest/api/content/{page_id}/history", auth=credentials, timeout=TIMEOUT)
            existing_content = get_page_content(confluence_url, page_id, credentials)
            new_content = existing_content + "<br />" + html
            data = get_html_payload(page_title, project_key, parent_page_id, new_content)
            if page_hist.status_code == 200:
                page_version = page_hist.json()['lastUpdated']['number']
            else:
                print(f"error: {page_hist.json()['message']}")
                exit(1)

            data['version'] = {'number': page_version + 1}
            update_url = f"{confluence_url}/rest/api/content/{page_id}"
            update_response = requests.put(update_url, json=data, auth=credentials, timeout=TIMEOUT)
            if update_response.status_code != 200:
                response_json = json.loads(update_response.text)
                print(f"Error: {response_json['message']}")
                exit(1)
            else:
                print(f"Updated existing Confluence page: {page_title}")
            return

    # Page doesn't exist, create a new one
    confluence_response = requests.post(f"{confluence_url}/rest/api/content/", json=data, auth=credentials, timeout=TIMEOUT)
    if confluence_response.status_code != 200:
        response_json = json.loads(confluence_response.text)
        print(f"Error: {response_json['message']}")
        exit(1)
    elif (confluence_response == 200):
        print(f"Created new Confluence page: {page_title}")

def create_jira_version(jira_api_base_url, jira_project_key, release_version, credentials):
    create_releases_url = f"{jira_api_base_url}/{constants.JIRA_VERSION_CREATE}"

    proj_id = get_project_id(jira_api_base_url, jira_project_key, credentials)

    data = {
        "archived": False,
        "releaseDate": "2010-07-06",
        "name": release_version,
        "description": f"Version {release_version}",
        "projectId": proj_id,
        "released": True
    }


    release_response = requests.post(create_releases_url, json= data, auth=credentials, timeout=TIMEOUT)

    if(release_response.status_code == 201):
        release_json = release_response.json()
    else:
        print(f"Error: {release_json.message}")
        exit(1)

def get_project_id(jira_api_base_url, jira_project_id, credentials):
    
    project = requests.get(f"{jira_api_base_url}{constants.JIRA_PROJECT_SEARCH}/{jira_project_id}", auth= credentials, timeout=TIMEOUT)

    project_json = project.json()

    return project_json['id']

def update_story_release_version(jira_api_base_url, story_no, version, credentials):

    data = {
        "fields" : {
            "fixVersions": [{
                "name": version
            }]
        }
    }

    update_response = requests.put(f"{jira_api_base_url}/{constants.JIRA_ISSUE}/{story_no}", json= data, auth= credentials)

    if update_response.status_code != 204:
        print(update_response.json())
        exit(1)

def get_page_content(confluence_api_base_url, page_id, credentials):
    page_content = requests.get(f"{confluence_api_base_url}/rest/api/content/{page_id}?expand=body.storage", auth=credentials, timeout=TIMEOUT)
    if page_content.status_code == 200:
        response_json = page_content.json()
        return response_json['body']["storage"]["value"]
    else:
        print(f"error: {page_content.json()['message']}")
        exit(1)

def main(): 
    ''' Script entry point '''

    args = config_cli_parser().parse_args()

    print(f"Release Version: {args.releaseVersion}")
    print(f"Atlassian User / Password: {args.atlassianUser} / {args.atlassianPassword}")
    print(f"Jira Project Key: {args.jiraProject}")
    print(f"Release Note Custom Field: {args.releaseNoteCustomField}")
    print(f"Confluence Space Name and Parent Page: {args.confluenceSpaceName} / {args.confluencePageAncestor}")
    print(f"Confluence REST API base URL: {args.confluenceAPI}")
    print(f"Jira REST API base URL: {args.jiraAPI}")

    stories_data = get_completed_stories(args.jiraAPI, args.jiraProject, (args.atlassianUser, args.atlassianPassword))

    release_notes_html = create_release_notes(stories_data, args.jiraAPI, args.releaseNoteCustomField)

    post_release_notes_content(release_notes_html, args.confluenceAPI, (args.atlassianUser, args.atlassianPassword), args.releaseVersion, args.confluenceSpaceName, args.confluencePageAncestor)

    release_id = get_release_id(args.jiraAPI, args.releaseVersion, args.jiraProject, (args.atlassianUser, args.atlassianPassword))
    if release_id is None:
        create_jira_version(args.jiraAPI, args.jiraProject, args.releaseVersion, (args.atlassianUser, args.atlassianPassword))

    for story in stories_data["issues"]:
        update_story_release_version(args.jiraAPI, story["key"], args.releaseVersion, (args.atlassianUser, args.atlassianPassword))

if __name__ == "__main__":
    main()