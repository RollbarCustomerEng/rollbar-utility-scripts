# _______________________________________________________________
# Get list of users with email, ID, and username
# _______________________________________________________________

# _______________________________________________________________
# Imports that are good to use
# _______________________________________________________________
import requests

# _______________________________________________________________
# Place your account read token here
# _______________________________________________________________
account_read_token = 'TOKEN'

# Execute API request and extract users from list
# _______________________________________________________________
def main():
    url = 'https://api.rollbar.com/api/1/users'

    headers = {
        'X-Rollbar-Access-Token': account_read_token
    }
    # Make the API call to get the list of Users
    response = requests.request('GET', url, headers = headers)

    response_data = response.json()
    user_list_file = open('user-list.txt', 'w')

    # Loop through the list of users and write their contents to the console and to a .txt file
    for i in response_data['result']['users']:
        print(i)
        user_list_file.write(str(i) + "\n")

    user_list_file.close()


if __name__ == "__main__":
    main()
