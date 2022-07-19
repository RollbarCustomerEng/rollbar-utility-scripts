# _______________________________________________________________
# Get list of project access tokens with "read" scope
# _______________________________________________________________

# _______________________________________________________________
# Imports that are good to use
# _______________________________________________________________
import requests

# _______________________________________________________________
# Place your account read token here
# _______________________________________________________________
account_read_token = 'TOKEN'

# Create RQL Job based on the query above
# _______________________________________________________________
def main():
    projects_endpoint = 'https://api.rollbar.com/api/1/projects'

    headers = {
        'X-Rollbar-Access-Token': account_read_token
    }
    # Doing the API call to get the list of Users
    response = requests.request('GET', projects_endpoint, headers=headers)

    response_data = response.json()
    ids = []
    for i in response_data['result']:
        ids.append(i['id'])

    project_list_file = open('project-list.txt', 'w')
    project_list_file.write('project_id, token' + '\n')
    for id in ids:
        endpoint = 'https://api.rollbar.com/api/1/project/' + str(id) + '/access_tokens'
        response = requests.request('GET', endpoint, headers=headers)
        response_json = response.json()
        for t in response_json['result']:
            # change this from "read" to another value to get different tokens
            if t['name'] == "read":
                project_list_file.write(str(id) + ',' + str(t['access_token']) + "\n")


    project_list_file.close()


if __name__ == "__main__":
    main()
