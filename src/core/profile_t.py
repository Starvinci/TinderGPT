"""
######################################################################
#                                                                    #
#  Starvnici Inc.                                                    #
#  Created on: 19.5.2024                                             #
#                                                                    #
#  This file is part of the Starvincis TinderBot project.            #
#                                                                    #
#  This software is the confidential and proprietary information     #
#  of Starvnici Inc. ("Confidential Information"). You shall not     #
#  disclose such Confidential Information and shall use it only in   #
#  accordance with the terms of the license agreement you entered    #
#  into with Starvnici Inc.                                          #
#                                                                    #
#  STARVNICI INC. MAKES NO REPRESENTATIONS OR WARRANTIES ABOUT THE   #
#  SUITABILITY OF THE SOFTWARE, EITHER EXPRESS OR IMPLIED, INCLUDING #
#  BUT NOT LIMITED TO THE IMPLIED WARRANTIES OF MERCHANTABILITY,     #
#  FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT.            #
#  STARVNICI INC. SHALL NOT BE LIABLE FOR ANY DAMAGES SUFFERED BY    #
#  LICENSEE AS A RESULT OF USING, MODIFYING OR DISTRIBUTING THIS     #
#  SOFTWARE OR ITS DERIVATIVES.                                      #
#                                                                    #
#  All rights reserved.                                              #
#                                                                    #
######################################################################
"""

import requests
import json

TINDER_URL = "https://api.gotinder.com/v2/profile?include=account%2Cuser"

def get_profile(token):
    headers = {
        "X-Auth-Token": token,
        "Content-type": "application/json"
    }
    response = requests.get("https://api.gotinder.com/v2/profile?include=account%2Cuser", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: Unable to fetch profile data. Status code: {response.status_code}")
        return None

def extract_profile_info(json_data):
    user = json_data['data']['user']
    
    name = user.get('name', 'Unbekannt')
    bio = user.get('bio', 'Keine Bio verfügbar')
    
    interests = [interest['name'] for interest in user.get('user_interests', {}).get('selected_interests', [])]
    interests_str = ', '.join(interests) if interests else 'Keine Interessen verfügbar'
    
    job = user.get('jobs', [{'title': {'name': 'Kein Beruf angegeben'}}])[0]['title']['name']
    location = user.get('city', {}).get('name', 'Unbekannter Standort')
    
    schools = [school['name'] for school in user.get('schools', [])]
    schools_str = ', '.join(schools) if schools else 'Keine Schulen verfügbar'
    
    profile_info = {
        "name": name,
        "bio": bio,
        "interests": interests_str,
        "job": job,
        "location": location,
        "schools": schools_str
    }
    
    profile_info_str = f"Name: {profile_info['name']}, Bio: {profile_info['bio']}, Interessen: {profile_info['interests']}, Beruf: {profile_info['job']}, Standort: {profile_info['location']}, Schule: {profile_info['schools']}"
    
    return profile_info_str

def main():
    token = "2e38fedd-5e87-48f2-b438-60152453af63"  # Replace with your Tinder Auth Token
    profile_data = get_profile(token)
    if profile_data:
        profile_info_str = extract_profile_info(profile_data)
        print(profile_info_str)

if __name__ == "__main__":
    main()
