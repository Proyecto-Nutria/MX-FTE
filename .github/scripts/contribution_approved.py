import json
import sys
import uuid
from datetime import datetime
import util
import re


def add_https_to_url(url):
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def getData(body, is_edit, username):
    lines = [text.strip("# ") for text in re.split('[\n\r]+', body)]
    
    data = {"date_updated": int(datetime.now().timestamp())}
    if "no response" not in lines[1].lower():
        data["url"] = add_https_to_url(lines[1].strip())
    if "no response" not in lines[3].lower():
        data["company_name"] = lines[3]
    if "no response" not in lines[5].lower():
        data["title"] = lines[5]
    if "no response" not in lines[7].lower():
        data["locations"] = [line.strip() for line in lines[7].split("|")]
    if "no response" not in lines[9].lower():
        data["level"] = [line.strip() for line in lines[9].split(",")]
    if "no response" not in lines[11].lower():
        data["english"] = "Dunno"
        for option in ["Yes", "No", "Dunno"]:
            if option in lines[11]:
                data["english"] = option
    if "none" not in lines[13].lower():
        data["active"] = "yes" in lines[13].lower()
    if is_edit:
        data["is_visible"] = "[x]" not in lines[15].lower()

    email = lines[17 if is_edit else 15].lower()
    if "no response" not in email:
        util.setOutput("commit_email", email)
        util.setOutput("commit_username", username)
    else:
        util.setOutput("commit_email", "action@github.com")
        util.setOutput("commit_username", "GitHub Action")
    
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
    issue_user = event_data['issue']['user']['login']

    data = getData(issue_body, is_edit=edit_job, username=issue_user)

    if new_job:
        data["source"] = issue_user
        data["id"] = str(uuid.uuid4())
        data["date_posted"] = int(datetime.now().timestamp())
        data["company_url"] = ""
        data["is_visible"] = True

    # remove utm-source
    utm = data["url"].find("?utm_source")
    if utm == -1:
        utm = data["url"].find("&utm_source")
    if utm != -1:
        data["url"] = data["url"][:utm]


    # UPDATE LISTINGS

    with open(".github/scripts/listings.json", "r") as f:
        listings = json.load(f)

    if listing_to_update := next(
        (item for item in listings if item["url"] == data["url"]), None
    ):
        if new_job:
            util.fail("This job is already in our list. See CONTRIBUTING.md for how to edit a listing")
        for key, value in data.items():
            listing_to_update[key] = value

        util.setOutput("commit_message", "updated listing: " + listing_to_update["title"] + " at " + listing_to_update["company_name"])
    else:
        if edit_job:
            util.fail("We could not find this job in our list. Please double check you inserted the right url")
        listings.append(data)
        util.setOutput("commit_message", "added listing: " + data["title"] + " at " + data["company_name"])

    with open(".github/scripts/listings.json", "w") as f:
        f.write(json.dumps(listings, indent=4))


if __name__ == "__main__":
    main()
