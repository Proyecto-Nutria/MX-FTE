import json
import sys
import util
import re


def add_https_to_url(url):
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def get_data(body):
    lines = [text.strip("# ") for text in re.split('[\n\r]+', body)]
    
    data = {}
    if "no response" not in lines[3].lower():
        data["company_name"] = lines[3]
    if "no response" not in lines[5].lower():
        data["title"] = lines[5]
    if "no response" not in lines[7].lower():
        data["locations"] = [line.strip() for line in lines[7].split("|")]
    
    return data


def main():
    event_file_path = sys.argv[1]

    with open(event_file_path) as f:
        event_data = json.load(f)


    # CHECK IF NEW OR OLD JOB

    new_job = "new_job" in [label["name"] for label in event_data["issue"]["labels"]]
    edit_job = "edit_job" in [label["name"] for label in event_data["issue"]["labels"]]

    if not new_job and not edit_job:
        util.fail("Only new_job and edit_job issues can be approved")

    # GET DATA FROM ISSUE FORM

    issue_body = event_data['issue']['body']

    data = get_data(issue_body)

    # remove utm-source
    utm = data["url"].find("?utm_source")
    if utm == -1:
        utm = data["url"].find("&utm_source")
    if utm != -1:
        data["url"] = data["url"][:utm]
    
    issue_title = "{} | {} | {} Location(s)".format(
        data.get('company_name', '?'), 
        data.get('title', '?'), 
        len(data.get('locations', [])),
    )
    print('data', data)
    print('issue_title', issue_title)

    util.setOutput("issue_title", issue_title)


if __name__ == "__main__":
    main()
