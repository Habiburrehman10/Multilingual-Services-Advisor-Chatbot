from flask import Flask, request, jsonify
from dialogflow_fulfillment import WebhookClient,  Payload, RichResponse, Card
import requests
import random
from google.cloud import dialogflow_v2
from google.api_core.exceptions import GoogleAPIError
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import os
import json
import pandas as pd
from googletrans import Translator
from dotenv import load_dotenv
load_dotenv()
#project_id = 'servicesadvisorhelpbot-a9hn'
project_id = 'romania-helpbot-hxyo'
import json

translator = Translator()


# from oauth2client import client
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './service_key.json'
# Load the service account key
with open('./service_key.json') as keyfile:
    key_data = json.load(keyfile)
key = os.getenv('OPEN_AI')
private_key = key_data['private_key'].replace('\\n', '\n')
# Replace with your Dialogflow project ID, session ID, and event name
event_name = 'catageIntent'
with open('category_names.json', 'r') as file:
    category_data = json.load(file)
session_client = dialogflow_v2.SessionsClient()
# services = [
#     {"Basic Needs": ["Blankets & Warm Clothes","Providing Hygiene Products", "Provision of Food","Social Market",{"Financial Assistance/ Cash and vouchers": ["Cash for cold weather fuel and items", "Cash for documentation", "Cash for education","Cash for food","Cash for health","Cash for rent","Monthly Cash Grants","Other Cash Assistance"]}]},
#     {"Cash Assistance": ["Multipurpose Cash Assistance","Multipurpose vouchers","Vouchers for education","Vouchers for medicine","Vouchers for protection","Vouchers for winterisation"]},
#     {"Shelter":["Shelter"]},
#     {"Education":["Language Classes","School Enrollment Assistance","Higher Education enrollment","Early Care","Educational centers"]},
#     {"Employment":["Job Trainings Programs","Job Placement Services","Language Classes","Day care for children services"]},
#     {"Healthcare":["Family Doctors","Medical Clinics","Hospitals","Infant Nutrition"]},
#     {"Mental Health Support": ["Individual Consultations","Psychiatrists","Specialized Services ( e.g Autism)","Addiction Support"]},
#     {"Legal Assistance":["Refugee Legal Aid","Individual Consultations","Support with Documentation"]},
#     {"Child Protection":["Child Protection"]}
# ]

def send_event_to_dialogflow(event_response,session_id):
    project_id = "romania-helpbot-hxyo"  # Replace with your Dialogflow project ID
    # session_id = "your-session-id"  # Replace with your Dialogflow session ID
    print(session_id)
    
    creds = session_client.GoogleCredentials.get_application_default()

    creds = creds.create_scoped(['https://www.googleapis.com/auth/cloud-platform',
                                'https://www.googleapis.com/auth/datastore',
                                'https://www.googleapis.com/auth/cloudkms'])

    access_token_info = None
    access_token_info = creds.get_access_token()
    access_token = access_token_info.access_token
    # # Load the service account key
    # credentials = service_account.Credentials.from_service_account_file(
    #     'service_key.json',
    #     scopes=["https://www.googleapis.com/auth/cloud-platform"],
    # )
    # print(credentials)
    # # Obtain an access token
    # access_token_info = credentials.refresh(Request())
    # print(access_token_info)
    # # Check if access_token_info is None
    # if access_token_info:
    #     access_token = access_token_info.token
    #     print(access_token)
    # else:
    #     print("Error refreshing access token.")
    #     return


    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "x-goog-user-project": project_id
    }

    api_url = f"https://dialogflow.googleapis.com/v2/projects/{project_id}/agent/sessions/{session_id}:detectIntent"

    # Make the API request to trigger the follow-up event
    response = requests.post(api_url, json=event_response, headers=headers)

    if response.status_code == 200:
        print("Follow-up event triggered successfully:", response.json())
    else:
        print("Error triggering follow-up event. Status code:", response.status_code)
        print("Response text:", response.text)
        print("Error triggering follow-up event:", response.text)
term_ids = {}


def find_actual_name(synonym):
    synonyms_for_locations = pd.read_excel('Synonyms_for_locations.xlsx')
    actual_name = synonyms_for_locations[synonyms_for_locations['Synonym'] == synonym]['Actual'].values
    if len(actual_name) > 0:
        return actual_name[0]
    else:
        return "No matching actual name found"


def fetch_location_data():
    url = f"https://romania.servicesadvisor.net/api/services/coordinates"
    try:
        # Make a GET request
        response = requests.get(url,verify=False)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse and return the response data (assuming it's JSON)
            response = response.json()
            return response
            # print(len(cities))
            # if "Craiova" in cities:
            #     print("Craiova is in the list")
            # else:
            #     print("Craiova is not in the list")
        else:
            # Print an error message if the request was not successful
            print(f"Error: {response.status_code}")
            return None
    except Exception as e:
        # Handle any exceptions that may occur during the request
        print(f"An error occurred: {e}")
        return None

def fetch_data(lang):
    url = f"https://romania.servicesadvisor.net/api/services/initialdata/{lang}"
    term_ids_list = []
    try:
        # Make a GET request
        response = requests.get(url,verify=False)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse and return the response data (assuming it's JSON)
            response = response.json()
            get_term = response['data']['terms']
            
            for term in get_term:
                if term['pid'] == 0:
                  term_ids[term['name']] = term['id']
            # for term in get_term:
            #     if(term['name'] == term_name):
            #         term_ids_list.append(term['id'])

            # print(term_ids)
            # # save it to txt 
            # with open('term_ids.txt', 'w') as file:
            #     file.write(json.dumps(term_ids))
            # return term_ids_list and response
            return response
            # print(len(cities))
            # if "Craiova" in cities:
            #     print("Craiova is in the list")
            # else:
            #     print("Craiova is not in the list")
        else:
            # Print an error message if the request was not successful
            print(f"Error: {response.status_code}")
            return None
    except Exception as e:
        # Handle any exceptions that may occur during the request
        print(f"An error occurred: {e}")
        return None
# fetch_data('en','Craiova')

result = fetch_data('en')

location_result = fetch_location_data()
global service_result
service_result = ''
def find_common_elements(list1, list2):
    set1 = set(list1)
    set2 = set(list2)
    
    common_elements = set1.intersection(set2)
    
    if len(common_elements) == 0:
        return None
    else:
        return common_elements
def check_availablity(city,service):
    city_services_data_list = []
    try:
      # Make a GET request
      # response = responsetwo
      # Check if the request was successful (status code 200)
      # Parse and return the response data (assuming it's JSON)
      response = location_result 
      # print(response['data'])
      get_term = response['data']
      # print(get_term)
      print("Checking for partner in the city")
      city_id = term_ids.get(city, None)
      print(city_id)
      if(city_id == None):
          return "No city found"
          
      partners = result['data']['partners']
      # city_id = fetch_data('en','Arad')
      # print(partners)
      for i in range(len(get_term)):
          city_services_data = {}
          # print(get_term[i]['did'] == city_id)
          if(get_term[i]['cid'] == city_id or get_term[i]['did'] == city_id):
              city_services_data = get_term[i]
              print(city_services_data)
              city_services_data_list.append(city_services_data)
              # break
              # break

      # service_id = term_ids[service]
      service_id = get_service_id(service)
      service_id = str(service_id)
      service_id = service_id.replace(" ", "")
      service_id = service_id.split(',')
      # service_id = service_id
      
      print(service_id)
      for i in city_services_data_list:
          city_services = i['t']
          city_services = city_services.split(',')
          ifexists = find_common_elements(city_services,service_id)
          print(ifexists)
          if ifexists != None:
              print("Service Found")
              print(i)
              return True
          else:
              print("Service Not Found")
              # return None
          # print(city_services)
          for partner in partners:
              if(partner['id'] == i['pid']):
                  partner_name = partner['name']
      if ifexists == None:
          return None
      print(partner_name)
      return partner_name
          # print(city_services)
          # find = 'Craiova'
            # # find = 'Blankets & Warm Clothes'
            # print(term_ids[find])
                
            # print(len(cities))
            # if "Craiova" in cities:
            #     print("Craiova is in the list")
            # else:
            #     print("Craiova is not in the list")
    except Exception as e:
        # Handle any exceptions that may occur during the request
        print(f"An error occurred: {e}")
        return None
    
# Example usage:
# lang_value = "tr"
# tag_value = "your_tag_value"

app = Flask(__name__)
# Read the Excel file into a DataFrame
df = pd.read_excel('serviceIds.xlsx')

# Convert the DataFrame to a dictionary with service names as keys and service IDs as values
service_ids = dict(zip(df['ENGLISH'], df['Service ID']))

# Function to get service ID by name
def get_service_id(service_name):
    if("Specialized Services" == service_name):
        print("Specialized Services TRUE")
    return service_ids.get(service_name, "Service not found")

# @app.route("/dialogflow", methods=["GET"])
# def dialogflow_get():
#     return jsonify({}), 200
global is_service
is_service = False
global location_request
location_request = ''
@app.route("/dialogflow", methods=["GET","POST"])
def dialogflow_post():
    req = request.get_json(silent=True, force=True)
    session_id = req['session'].split('/')[-1]
    user_text = request.json['queryResult']['queryText']
    #get training phrases
    intent_name = req['queryResult']['intent']['displayName']
    # print(user_language)
    print(intent_name)
    print("user_text => ",user_text)
    agent = WebhookClient(req)
    print(agent)
    print(req)
    # Replace these values with your own
    def convo_end(agent):
        convo_end = translator.translate('Thank You for using our service.', dest=user_language).text
        agent.add(convo_end)

    # def get_service_name(agent):
    #     # user_message = agent.request['queryResult']['queryText']
    #     user_message = request.json['queryResult']['queryText']
    #     # user_message = "some education cash service"
    #     completion = client.chat.completions.create(
    #     model="gpt-3.5-turbo",
    #     messages=[
    #         {"role": "system", "content": f"You are a chatbot assistant for a services advisor company. the user will tell you the service they want may be they are do not know what they want so you will unerstand their need and return the name of the service they are looking for from the given data, data is: {services}, do not give suggestions or more answer just give one word or one value from the data."},
    #         {"role": "user", "content": user_message}
    #     ]
    # )   
        # global response
        # response = completion.choices[0].message.content
        # agent.add(str(response))
        # global is_service
        # is_service = True
        # getlocation(agent)
    
    def get_city_name(agent):
        user_message = request.json['queryResult']['queryText']
        user_message = user_message.capitalize()
        user_message = find_actual_name(user_message)
        global user_language

        global location_request
        location_request = user_message
        print(user_message,user_service)
        partner = check_availablity(user_message,user_service)
        if partner == None and user_service == "Violence Support":
             # back to options button
            custom_payload = {
                "richContent": [
                  [
                    {
                      "type": "chips",
                      "options": [
                        {
                          "text": translator.translate('Back to Options', dest=user_language).text
                        },
                        {
                          "text": translator.translate('Start Again!', dest=user_language).text
                        }
                        
                      ]
                    }
                  ]
                ]
              }
            translated_no = translator.translate('No organizations found in this county. Try another \n Call this national level GBV Hotlines:\n \n +40 736 380 879\n(Anais)\n021 3114636 (Sensiblu)\n0747 297 988 (VIS)', dest=user_language).text
            agent.add(translated_no)
            agent.add(Payload(custom_payload))
            return
        elif partner == None and (user_service == "Individual Child Protection Services" or user_service == "Legal services for children (free legal aid)"):
             # back to options button
            custom_payload = {
                "richContent": [
                  [
                    {
                      "type": "chips",
                      "options": [
                        {
                          "text": translator.translate('Back to Options', dest=user_language).text
                        },
                        {
                          "text": translator.translate('Start Again!', dest=user_language).text
                        }
                      ]
                    }
                  ]
                ]
              }
            translated_no = translator.translate('No organizations found in this county. Try another \n Call 119 for Child Protection', dest=user_language).text
            agent.add(translated_no)
            agent.add(Payload(custom_payload))
            return
        elif partner == "No city found":
            custom_payload = {
                "richContent": [
                  [
                    {
                      "type": "chips",
                      "options": [
                        {
                          "text": translator.translate('Back to Options', dest=user_language).text
                        },
                        {
                          "text": translator.translate('Start Again!', dest=user_language).text
                        }
                      ]
                    }
                  ]
                ]
              }
            translated_no = translator.translate('Please try again, maybe you made a typo', dest=user_language).text
            agent.add(translated_no)
            agent.add(Payload(custom_payload))
            return
        elif partner == None:
            # back to options button
            custom_payload = {
                "richContent": [
                  [
                    {
                      "type": "chips",
                      "options": [
                        {
                          "text": translator.translate('Back to Options', dest=user_language).text
                        },
                        {
                          "text": translator.translate('Start Again!', dest=user_language).text
                        }
                      ]
                    }
                  ]
                ]
              }
            translated_no = translator.translate('The service you are searching is not available in this county, try another', dest=user_language).text
            agent.add(translated_no)
            agent.add(Payload(custom_payload))
            return
            
        result = get_service_id(user_service)
        result = str(result)
        print(type(result))
        result = result.replace(" ", "")
        
        # print(f"The service ID for '{user_service}' is: {result}")

        print(term_ids[user_message])

        if partner != None:
          global service_result
          service_result = f"https://romania.servicesadvisor.net/{user_language}/search?category={result}&location={term_ids[user_message]}"
          view_result(agent)
          # agent.add("Please click to view the results.")
          # custom_payload = {
          #   "richContent": [
          #     [
          #       {
          #         "type": "chips",
          #         "options": [
          #           {
          #             "text": "View Services"
          #           }
          #         ]
          #       }
          #     ]
          #   ]
          # }
          # agent.add(Payload(custom_payload))

        # global partner_name
    def view_result(agent):
        global user_language    
        global service_result
        global location_request
        print(service_result)
        result_translate = translator.translate(f"{user_service} in {location_request}", dest=user_language).text
        custom_payload = {
            "richContent": [
              [
                {
                  "type": "chips",
                  "options": [
                    {
                      "text": f"{result_translate}",
                      "image": {
                        "src": {
                          "rawUrl": "https://romania.servicesadvisor.net/assets/img/logo.png"
                        }
                      },
                      "link": service_result
                    }
                  ]
                }
              ]
            ]
          }
        agent.add(Payload(custom_payload))
        translated = translator.translate('Do you want to try another county?', dest=user_language).text
        # agent.add(f"Do you want to try another city?")
        agent.add(translated)
        yes = translator.translate('Yes', dest=user_language).text
        no = translator.translate('No', dest=user_language).text
        custom_payload2 = {
            "richContent": [
              [
                {
                  "type": "chips",
                  "options": [
                    {
                      "text": f"{yes.capitalize()}"
                    },
                    {
                      "text": f"{no.capitalize()}"
                    },
                      {
                        "text": translator.translate('Start Again!', dest=user_language).text
                      }
                  ]
                }
              ]
            ]
          }
        agent.add(Payload(custom_payload2))
    def setLanguage(agent):
        global user_language

        if(user_text.lower() in ["english","start again!","back to options"]):
            user_language = "en"
            translatedText = "Welcome to the Services Advisor Helpbot!\nI'm here to assist  you. This conversation is not going to be recorded"
            custom_payload = {
              "richContent": [
                [
                  {
                    "options": [
                      {
                        "text": "Looking for Service"
                      },
                      {
                        "text": "I am in Danger"
                      }
                    ],
                    "type": "chips"
                  }
                ]
              ]
            }
            
        elif(user_text.lower() in ["romanian","română","începeți din nou!","înapoi la opțiuni"]):
            user_language = "ro"
            translatedText = "Bine ați venit la Services Advisor Helpbot!\nSunt aici pentru a vă ajuta\nAceastă conversație nu va fi înregistrată"
            custom_payload = {
              "richContent": [
                [
                  {
                    "options": [
                      {
                        "text": "Căutarea serviciului"
                      },
                      {
                        "text": "Sunt în pericol"
                      }
                    ],
                    "type": "chips"
                  }
                ]
              ]
            }
        elif(user_text.lower() in ["russian","русский","начни заново!","начни снова!","вернуться к вариантам","вернемся к опциям"]):
            user_language = "ru"
            translatedText = "Добро пожаловать в справочный бот Service Advisor Helpbot!\nЯ здесь, чтобы помочь вам. Этот разговор не будет записан"
            custom_payload = {
              "richContent": [
                [
                  {
                    "options": [
                      {
                        "text": "Ищу услугу"
                      },
                      {
                        "text": "Я в опасности"
                      }
                    ],
                    "type": "chips"
                  }
                ]
              ]
            }

        elif(user_text.lower() in ["ukrainian","українська","почати знову!","почніть знову!","повернутися до варіантів"]):
            user_language = "uk"
            translatedText = "Ласкаво просимо до довідкового бота Service Advisor Helpbot!\nЯ тут, щоб допомогти вам. Ця розмова не буде записана"
            custom_payload = {
              "richContent": [
                [
                  {
                    "options": [
                      {
                        "text": "Шукаю послугу"
                      },
                      {
                        "text": "Я в небезпеці"
                      }
                    ],
                    "type": "chips"
                  }
                ]
              ]
            }

            
        print(user_language)
        print(req)
        # change the request language
        req['queryResult']['languageCode'] = user_language
        print(req)
        agent.add(translatedText)
        agent.add(Payload(custom_payload))              
        return
    def getlocation(agent):
        global is_service
        global user_language
        print(is_service)
        global user_service
        translated_yes = translator.translate('Yes', dest=user_language).text
        translated_yes = translated_yes.capitalize()
        if request.json['queryResult']['queryText'] != translated_yes:

          user_service = category_data[intent_name]

        # if is_service:
        #     user_service = response
        cities=[]
        if result:
            for i in range(10):
                # get random 10 terms
                cities.append(random.choice(result['data']['terms'])['name'])
    
        # print("intent => hi")
        # if(user_language == "ro"):
        print(user_language)
        print(req)
        pay_load_start_again = translator.translate('Start Again!', dest=user_language).text
        custom_payload = {
          "richContent": [
            [
              {
                "type": "chips",
                "options": [
                  {
                    "text": pay_load_start_again
                  }
                ]
              }
            ]
          ]
        }
        translated = translator.translate('What is your location? \n \n Type the name of the county where you are now', dest=user_language).text
        agent.add(translated)
        agent.add(Payload(custom_payload))
        return
        # agent.add(f'What is your location? \n \n Type the name of the city/locality where you are now')
    def restart_convo(agent):
        restart_text = translator.translate('Do you want to try another service?', dest=user_language).text
        custom_payload = {
          "richContent": [
            [
              {
                "type": "chips",
                "options": [
                  {
                    "text": translator.translate('Yes.', dest=user_language).text
                  },
                  {
                    "text": translator.translate('No', dest=user_language).text
                  },
                  {
                    "text": translator.translate('Start Again!', dest=user_language).text
                  }
                ]
              }
            ]
          ]
        }
        agent.add(restart_text)
        agent.add(Payload(custom_payload))
        return
    def thankyou_rating(agent):
        restart_text = translator.translate('Thank you for speaking with us. Please take a moment to rate the conversation. (1 to 5)', dest=user_language).text
        custom_payload = {
          "richContent": [
            [
              {
                "type": "chips",
                "options": [
                  {
                    "text": "5"
                  },
                  {
                    "text": "4"
                  },
                  {
                    "text": "3"
                  },
                  {
                    "text": "2"
                  },
                  {
                    "text": "1"
                  }
                ]
              }
            ]
          ]
        }
        agent.add(restart_text)
        agent.add(Payload(custom_payload))
        return

    intent_map = {
        'Language - English': setLanguage,
        'Language - Romania': setLanguage,
        'Language - Russian': setLanguage,
        'Language - Ukrainian': setLanguage,
        'Language - English - service - yes - DistHumAid - BWC': getlocation,
        'Language - English - service - yes - DistHumAid - HygieneProducts': getlocation,
        'Language - English - service - yes - DistHumAid - provisionofFood': getlocation,
        'Language - English - service - yes - DistHumAid - socialMarket': getlocation,
        'Language - English - service - yes - shelter': getlocation,
        'Language - English - service - yes - cashAss - multiVouch': getlocation,
        'Language - English - service - yes - cashAss - vouchProt': getlocation,
        'Language - English - service - yes - cashAss - vouchEdu': getlocation,
        'Language - English - service - yes - cashAss - vouchWinter': getlocation,
        'Language - English - service - yes - cashAss - vouchMed': getlocation,
        'Language - English - service - yes - cashAss - cashprot': getlocation,
        'Language - English - service - yes - cashAss - multiCashAss': getlocation,
        'Language - English - service - yes - DistHumAid - FinancAssis - rent': getlocation,
        'Language - English - service - yes - DistHumAid - FinancAssis - OCA': getlocation,
        'Language - English - service - yes - DistHumAid - FinancAssis - somediff': getlocation,
        'Language - English - service - yes - DistHumAid - FinancAssis - food': getlocation,
        'Language - English - service - yes - DistHumAid - FinancAssis - health': getlocation,
        'Language - English - service - yes - DistHumAid - FinancAssis - education': getlocation,
        'Language - English - service - yes - DistHumAid - FinancAssis - cashgrants': getlocation,
        'Language - English - service - yes - DistHumAid - FinancAssis - docs': getlocation,
        'Language - English - service - yes - DistHumAid - FinancAssis - ColdWeatherFuelAndItems': getlocation,
        'Language - English - service - yes - education - HighEduenroll': getlocation,
        'Language - English - service - yes - education - SchlEnrollAssis': getlocation,
        'Language - English - service - yes - employment - LanguageClasses': getlocation,
        'Language - English - service - yes - employment - jobtrainprog': getlocation,
        'Language - English - service - yes - employment - JobPlacementServices': getlocation,
        'Language - English - service - yes - healthcare - Hospitals': getlocation,
        'Language - English - service - yes - mentalHealth - Specialized Services': getlocation,
        'Language - English - service - yes - mentalHealth - Psychiatrists': getlocation,
        'Language - English - service - yes - mentalHealth - IndividualConsultations': getlocation,
        'Language - English - service - yes - legalAssis - Refugee Legal Aid': getlocation,
        'Language - English - service - yes - legalAssis - Individual Consultations': getlocation,
        'Language - English - service - yes - legalAssis - Support With Documentation': getlocation,
        'Language - English - service - yes - shelter - TempAccom': getlocation,
        'Language - English - service - yes - shelter - Cash for Emer Rent': getlocation,
        'Language - English - service - yes - Financial Assistance': getlocation,
        'Language - English - service - yes - education - languageClasses': getlocation,
        'Language - English - service - yes - education - School materials': getlocation,
        'Language - English - service - yes - education - Adult education': getlocation,
        'Language - English - service - yes - education - EarlyCare': getlocation,
        'Language - English - service - yes - education - Educenters': getlocation,
        'Language - English - service - yes - education - Skills development': getlocation,
        'Language - English - service - yes - education - Education for children with disabilities': getlocation,
        'Language - English - service - yes - education - SchlEnrollAssis': getlocation,
        'Language - English - service - yes - education - Recreational Activities': getlocation,
        'Language - English - service - yes - education - Parental support': getlocation,
        'Language - English - service - yes - education - After-school': getlocation,
        'Language - English - service - yes - Youth   Activities': getlocation,
        'Language - English - service - yes - childprotect - Legal services for children (free legal aid)': getlocation,
        'Language - English - service - yes - childprotect - Individual   Child Protection Services': getlocation,
        'Language - English - service - yes - employment - Daycareforchildrenservices': getlocation,
        'Language - English - service - yes - employment - Day care for elderly and people with disabilities': getlocation,
        'Language - English - service - yes - employment - LanguageClasses': getlocation,
        'Language - English - service - yes - employment - jobtrainprog': getlocation,
        'Language - English - service - yes - employment - JobPlacementServices': getlocation,
        'Language - English - service - yes - employment - Legal Support to access work': getlocation,
        'Language - English - service - yes - healthcare - Maternal & newborn health': getlocation,
        'Language - English - service - yes - healthcare - Pediatrics': getlocation,
        'Language - English - service - yes - healthcare - MedicalClinics': getlocation,
        'Language - English - service - yes - healthcare - Secondary  & tertiary Care': getlocation,
        'Language - English - service - yes - healthcare - Health Support': getlocation,
        'Language - English - service - yes - healthcare - Communicable diseases': getlocation,
        'Language - English - service - yes - healthcare - Medical tests': getlocation,
        'Language - English - service - yes - healthcare - Medicines': getlocation,
        'Language - English - service - yes - healthcare - Primary care': getlocation,
        'Language - English - service - yes - healthcare - Non communicable diseases': getlocation,
        'Language - English - service - yes - healthcare - Sexual violence': getlocation,
        'Language - English - service - yes - healthcare - Recovery': getlocation,
        'Language - English - service - yes - healthcare - Hospitals': getlocation,
        'Language - English - service - yes - healthcare - STI & HIV/AIDS': getlocation,
        'Language - English - service - yes - mentalHealth - Group   counselling': getlocation,
        'Language - English - service - yes - mentalHealth - Specialized Services': getlocation,
        'Language - English - service - yes - mentalHealth - Psychiatrists': getlocation,
        'Language - English - service - yes - mentalHealth - Support for children and youth': getlocation,
        'Language - English - service - yes - mentalHealth - IndividualConsultations': getlocation,
        'Language - English - service - yes - Disability-Specific   Services': getlocation,
        'Language - English - service - yes - Violence   Support': getlocation,
        'Language - English - service - yes - legalAssis - Refugee Legal Aid': getlocation,
        'Language - English - service - yes - legalAssis - Individual Consultations': getlocation,
        'Language - English - service - yes - legalAssis - Human Trafficking support': getlocation,
        'Language - English - service - yes - legalAssis - Support with Documentation': getlocation,
        'Language - English - service - yes - Community Centers/Services': getlocation,
        
        'Language - Romania - service - yes - DistHumAid - BWC': getlocation,
        'Language - Romania - service - yes - DistHumAid - HygieneProducts': getlocation,
        'Language - Romania - service - yes - DistHumAid - provisionofFood': getlocation,
        'Language - Romania - service - yes - DistHumAid - socialMarket': getlocation,
        'Language - Romania - service - yes - shelter': getlocation,
        'Language - Romania - service - yes - cashAss - multiVouch': getlocation,
        'Language - Romania - service - yes - cashAss - vouchProt': getlocation,
        'Language - Romania - service - yes - cashAss - vouchEdu': getlocation,
        'Language - Romania - service - yes - cashAss - vouchWinter': getlocation,
        'Language - Romania - service - yes - cashAss - vouchMed': getlocation,
        'Language - Romania - service - yes - cashAss - cashprot': getlocation,
        'Language - Romania - service - yes - cashAss - multiCashAss': getlocation,
        'Language - Romania - service - yes - DistHumAid - FinancAssis - rent': getlocation,
        'Language - Romania - service - yes - DistHumAid - FinancAssis - OCA': getlocation,
        'Language - Romania - service - yes - DistHumAid - FinancAssis - somediff': getlocation,
        'Language - Romania - service - yes - DistHumAid - FinancAssis - food': getlocation,
        'Language - Romania - service - yes - DistHumAid - FinancAssis - health': getlocation,
        'Language - Romania - service - yes - DistHumAid - FinancAssis - education': getlocation,
        'Language - Romania - service - yes - DistHumAid - FinancAssis - cashgrants': getlocation,
        'Language - Romania - service - yes - DistHumAid - FinancAssis - docs': getlocation,
        'Language - Romania - service - yes - DistHumAid - FinancAssis - ColdWeatherFuelAndItems': getlocation,
        'Language - Romania - service - yes - education - HighEduenroll': getlocation,
        'Language - Romania - service - yes - education - SchlEnrollAssis': getlocation,
        'Language - Romania - service - yes - employment - LanguageClasses': getlocation,
        'Language - Romania - service - yes - employment - jobtrainprog': getlocation,
        'Language - Romania - service - yes - employment - JobPlacementServices': getlocation,
        'Language - Romania - service - yes - healthcare - Hospitals': getlocation,
        'Language - Romania - service - yes - mentalHealth - Specialized Services': getlocation,
        'Language - Romania - service - yes - mentalHealth - Psychiatrists': getlocation,
        'Language - Romania - service - yes - mentalHealth - IndividualConsultations': getlocation,
        'Language - Romania - service - yes - legalAssis - Refugee Legal Aid': getlocation,
        'Language - Romania - service - yes - legalAssis - Individual Consultations': getlocation,
        'Language - Romania - service - yes - legalAssis - Support With Documentation': getlocation,
        'Language - Romania - service - yes - shelter - TempAccom': getlocation,
        'Language - Romania - service - yes - shelter - Cash for Emer Rent': getlocation,
        'Language - Romania - service - yes - Financial Assistance': getlocation,
        'Language - Romania - service - yes - education - languageClasses': getlocation,
        'Language - Romania - service - yes - education - School materials': getlocation,
        'Language - Romania - service - yes - education - Adult education': getlocation,
        'Language - Romania - service - yes - education - EarlyCare': getlocation,
        'Language - Romania - service - yes - education - Educenters': getlocation,
        'Language - Romania - service - yes - education - Skills development': getlocation,
        'Language - Romania - service - yes - education - Education for children with disabilities': getlocation,
        'Language - Romania - service - yes - education - SchlEnrollAssis': getlocation,
        'Language - Romania - service - yes - education - Recreational Activities': getlocation,
        'Language - Romania - service - yes - education - Parental support': getlocation,
        'Language - Romania - service - yes - education - After-school': getlocation,
        'Language - Romania - service - yes - Youth   Activities': getlocation,
        'Language - Romania - service - yes - childprotect - Legal services for children (free legal aid)': getlocation,
        'Language - Romania - service - yes - childprotect - Individual   Child Protection Services': getlocation,
        'Language - Romania - service - yes - employment - Daycareforchildrenservices': getlocation,
        'Language - Romania - service - yes - employment - Day care for elderly and people with disabilities': getlocation,
        'Language - Romania - service - yes - employment - LanguageClasses': getlocation,
        'Language - Romania - service - yes - employment - jobtrainprog': getlocation,
        'Language - Romania - service - yes - employment - JobPlacementServices': getlocation,
        'Language - Romania - service - yes - employment - Legal Support to access work': getlocation,
        'Language - Romania - service - yes - healthcare - Maternal & newborn health': getlocation,
        'Language - Romania - service - yes - healthcare - Pediatrics': getlocation,
        'Language - Romania - service - yes - healthcare - MedicalClinics': getlocation,
        'Language - Romania - service - yes - healthcare - Secondary  & tertiary Care': getlocation,
        'Language - Romania - service - yes - healthcare - Health Support': getlocation,
        'Language - Romania - service - yes - healthcare - Communicable diseases': getlocation,
        'Language - Romania - service - yes - healthcare - Medical tests': getlocation,
        'Language - Romania - service - yes - healthcare - Medicines': getlocation,
        'Language - Romania - service - yes - healthcare - Primary care': getlocation,
        'Language - Romania - service - yes - healthcare - Non communicable diseases': getlocation,
        'Language - Romania - service - yes - healthcare - Sexual violence': getlocation,
        'Language - Romania - service - yes - healthcare - Recovery': getlocation,
        'Language - Romania - service - yes - healthcare - Hospitals': getlocation,
        'Language - Romania - service - yes - healthcare - STI & HIV/AIDS': getlocation,
        'Language - Romania - service - yes - mentalHealth - Group   counselling': getlocation,
        'Language - Romania - service - yes - mentalHealth - Specialized Services': getlocation,
        'Language - Romania - service - yes - mentalHealth - Psychiatrists': getlocation,
        'Language - Romania - service - yes - mentalHealth - Support for children and youth': getlocation,
        'Language - Romania - service - yes - mentalHealth - IndividualConsultations': getlocation,
        'Language - Romania - service - yes - Disability-Specific   Services': getlocation,
        'Language - Romania - service - yes - Violence   Support': getlocation,
        'Language - Romania - service - yes - legalAssis - Refugee Legal Aid': getlocation,
        'Language - Romania - service - yes - legalAssis - Individual Consultations': getlocation,
        'Language - Romania - service - yes - legalAssis - Human Trafficking support': getlocation,
        'Language - Romania - service - yes - legalAssis - Support with Documentation': getlocation,
        'Language - Romania - service - yes - Community Centers/Services': getlocation,

        'Language - Russian - service - yes - DistHumAid - HygieneProducts': getlocation,
        'Language - Russian - service - yes - DistHumAid - BWC': getlocation,
        'Language - Russian - service - yes - DistHumAid - provisionofFood': getlocation,
        'Language - Russian - service - yes - DistHumAid - socialMarket': getlocation,
        'Language - Russian - service - yes - shelter': getlocation,
        'Language - Russian - service - yes - cashAss - multiVouch': getlocation,
        'Language - Russian - service - yes - cashAss - vouchProt': getlocation,
        'Language - Russian - service - yes - cashAss - vouchEdu': getlocation,
        'Language - Russian - service - yes - cashAss - vouchWinter': getlocation,
        'Language - Russian - service - yes - cashAss - vouchMed': getlocation,
        'Language - Russian - service - yes - cashAss - cashprot': getlocation,
        'Language - Russian - service - yes - cashAss - multiCashAss': getlocation,
        'Language - Russian - service - yes - DistHumAid - FinancAssis - rent': getlocation,
        'Language - Russian - service - yes - DistHumAid - FinancAssis - OCA': getlocation,
        'Language - Russian - service - yes - DistHumAid - FinancAssis - somediff': getlocation,
        'Language - Russian - service - yes - DistHumAid - FinancAssis - food': getlocation,
        'Language - Russian - service - yes - DistHumAid - FinancAssis - health': getlocation,
        'Language - Russian - service - yes - DistHumAid - FinancAssis - education': getlocation,
        'Language - Russian - service - yes - DistHumAid - FinancAssis - cashgrants': getlocation,
        'Language - Russian - service - yes - DistHumAid - FinancAssis - docs': getlocation,
        'Language - Russian - service - yes - DistHumAid - FinancAssis - ColdWeatherFuelAndItems': getlocation,
        'Language - Russian - service - yes - education - HighEduenroll': getlocation,
        'Language - Russian - service - yes - education - SchlEnrollAssis': getlocation,
        'Language - Russian - service - yes - employment - LanguageClasses': getlocation,
        'Language - Russian - service - yes - employment - jobtrainprog': getlocation,
        'Language - Russian - service - yes - employment - JobPlacementServices': getlocation,
        'Language - Russian - service - yes - healthcare - Hospitals': getlocation,
        'Language - Russian - service - yes - mentalHealth - Specialized Services': getlocation,
        'Language - Russian - service - yes - mentalHealth - Psychiatrists': getlocation,
        'Language - Russian - service - yes - mentalHealth - IndividualConsultations': getlocation,
        'Language - Russian - service - yes - legalAssis - Refugee Legal Aid': getlocation,
        'Language - Russian - service - yes - legalAssis - Individual Consultations': getlocation,
        'Language - Russian - service - yes - legalAssis - Support With Documentation': getlocation,
        'Language - Russian - service - yes - shelter - TempAccom': getlocation,
        'Language - Russian - service - yes - shelter - Cash for Emer Rent': getlocation,
        'Language - Russian - service - yes - Financial Assistance': getlocation,
        'Language - Russian - service - yes - education - languageClasses': getlocation,
        'Language - Russian - service - yes - education - School materials': getlocation,
        'Language - Russian - service - yes - education - Adult education': getlocation,
        'Language - Russian - service - yes - education - EarlyCare': getlocation,
        'Language - Russian - service - yes - education - Educenters': getlocation,
        'Language - Russian - service - yes - education - Skills development': getlocation,
        'Language - Russian - service - yes - education - Education for children with disabilities': getlocation,
        'Language - Russian - service - yes - education - SchlEnrollAssis': getlocation,
        'Language - Russian - service - yes - education - Recreational Activities': getlocation,
        'Language - Russian - service - yes - education - Parental support': getlocation,
        'Language - Russian - service - yes - education - After-school': getlocation,
        'Language - Russian - service - yes - Youth   Activities': getlocation,
        'Language - Russian - service - yes - childprotect - Legal services for children (free legal aid)': getlocation,
        'Language - Russian - service - yes - childprotect - Individual   Child Protection Services': getlocation,
        'Language - Russian - service - yes - employment - Daycareforchildrenservices': getlocation,
        'Language - Russian - service - yes - employment - Day care for elderly and people with disabilities': getlocation,
        'Language - Russian - service - yes - employment - LanguageClasses': getlocation,
        'Language - Russian - service - yes - employment - jobtrainprog': getlocation,
        'Language - Russian - service - yes - employment - JobPlacementServices': getlocation,
        'Language - Russian - service - yes - employment - Legal Support to access work': getlocation,
        'Language - Russian - service - yes - healthcare - Maternal & newborn health': getlocation,
        'Language - Russian - service - yes - healthcare - Pediatrics': getlocation,
        'Language - Russian - service - yes - healthcare - MedicalClinics': getlocation,
        'Language - Russian - service - yes - healthcare - Secondary  & tertiary Care': getlocation,
        'Language - Russian - service - yes - healthcare - Health Support': getlocation,
        'Language - Russian - service - yes - healthcare - Communicable diseases': getlocation,
        'Language - Russian - service - yes - healthcare - Medical tests': getlocation,
        'Language - Russian - service - yes - healthcare - Medicines': getlocation,
        'Language - Russian - service - yes - healthcare - Primary care': getlocation,
        'Language - Russian - service - yes - healthcare - Non communicable diseases': getlocation,
        'Language - Russian - service - yes - healthcare - Sexual violence': getlocation,
        'Language - Russian - service - yes - healthcare - Recovery': getlocation,
        'Language - Russian - service - yes - healthcare - Hospitals': getlocation,
        'Language - Russian - service - yes - healthcare - STI & HIV/AIDS': getlocation,
        'Language - Russian - service - yes - mentalHealth - Group   counselling': getlocation,
        'Language - Russian - service - yes - mentalHealth - Specialized Services': getlocation,
        'Language - Russian - service - yes - mentalHealth - Psychiatrists': getlocation,
        'Language - Russian - service - yes - mentalHealth - Support for children and youth': getlocation,
        'Language - Russian - service - yes - mentalHealth - IndividualConsultations': getlocation,
        'Language - Russian - service - yes - Disability-Specific   Services': getlocation,
        'Language - Russian - service - yes - Violence   Support': getlocation,
        'Language - Russian - service - yes - legalAssis - Refugee Legal Aid': getlocation,
        'Language - Russian - service - yes - legalAssis - Individual Consultations': getlocation,
        'Language - Russian - service - yes - legalAssis - Human Trafficking support': getlocation,
        'Language - Russian - service - yes - legalAssis - Support with Documentation': getlocation,
        'Language - Russian - service - yes - Community Centers/Services': getlocation,

        'Language - Ukrainian - service - yes - DistHumAid - HygieneProducts': getlocation,
        'Language - Ukrainian - service - yes - DistHumAid - BWC': getlocation,
        'Language - Ukrainian - service - yes - DistHumAid - provisionofFood': getlocation,
        'Language - Ukrainian - service - yes - DistHumAid - socialMarket': getlocation,
        'Language - Ukrainian - service - yes - shelter': getlocation,
        'Language - Ukrainian - service - yes - cashAss - multiVouch': getlocation,
        'Language - Ukrainian - service - yes - cashAss - vouchProt': getlocation,
        'Language - Ukrainian - service - yes - cashAss - vouchEdu': getlocation,
        'Language - Ukrainian - service - yes - cashAss - vouchWinter': getlocation,
        'Language - Ukrainian - service - yes - cashAss - vouchMed': getlocation,
        'Language - Ukrainian - service - yes - cashAss - cashprot': getlocation,
        'Language - Ukrainian - service - yes - cashAss - multiCashAss': getlocation,
        'Language - Ukrainian - service - yes - DistHumAid - FinancAssis - rent': getlocation,
        'Language - Ukrainian - service - yes - DistHumAid - FinancAssis - OCA': getlocation,
        'Language - Ukrainian - service - yes - DistHumAid - FinancAssis - somediff': getlocation,
        'Language - Ukrainian - service - yes - DistHumAid - FinancAssis - food': getlocation,
        'Language - Ukrainian - service - yes - DistHumAid - FinancAssis - health': getlocation,
        'Language - Ukrainian - service - yes - DistHumAid - FinancAssis - education': getlocation,
        'Language - Ukrainian - service - yes - DistHumAid - FinancAssis - cashgrants': getlocation,
        'Language - Ukrainian - service - yes - DistHumAid - FinancAssis - docs': getlocation,
        'Language - Ukrainian - service - yes - DistHumAid - FinancAssis - ColdWeatherFuelAndItems': getlocation,
        'Language - Ukrainian - service - yes - education - HighEduenroll': getlocation,
        'Language - Ukrainian - service - yes - education - SchlEnrollAssis': getlocation,
        'Language - Ukrainian - service - yes - employment - LanguageClasses': getlocation,
        'Language - Ukrainian - service - yes - employment - jobtrainprog': getlocation,
        'Language - Ukrainian - service - yes - employment - JobPlacementServices': getlocation,
        'Language - Ukrainian - service - yes - healthcare - Hospitals': getlocation,
        'Language - Ukrainian - service - yes - mentalHealth - Specialized Services': getlocation,
        'Language - Ukrainian - service - yes - mentalHealth - Psychiatrists': getlocation,
        'Language - Ukrainian - service - yes - mentalHealth - IndividualConsultations': getlocation,
        'Language - Ukrainian - service - yes - legalAssis - Refugee Legal Aid': getlocation,
        'Language - Ukrainian - service - yes - legalAssis - Individual Consultations': getlocation,
        'Language - Ukrainian - service - yes - legalAssis - Support With Documentation': getlocation,
        'Language - Ukrainian - service - yes - shelter - TempAccom': getlocation,
        'Language - Ukrainian - service - yes - shelter - Cash for Emer Rent': getlocation,
        'Language - Ukrainian - service - yes - Financial Assistance': getlocation,
        'Language - Ukrainian - service - yes - education - languageClasses': getlocation,
        'Language - Ukrainian - service - yes - education - School materials': getlocation,
        'Language - Ukrainian - service - yes - education - Adult education': getlocation,
        'Language - Ukrainian - service - yes - education - EarlyCare': getlocation,
        'Language - Ukrainian - service - yes - education - Educenters': getlocation,
        'Language - Ukrainian - service - yes - education - Skills development': getlocation,
        'Language - Ukrainian - service - yes - education - Education for children with disabilities': getlocation,
        'Language - Ukrainian - service - yes - education - SchlEnrollAssis': getlocation,
        'Language - Ukrainian - service - yes - education - Recreational Activities': getlocation,
        'Language - Ukrainian - service - yes - education - Parental support': getlocation,
        'Language - Ukrainian - service - yes - education - After-school': getlocation,
        'Language - Ukrainian - service - yes - Youth   Activities': getlocation,
        'Language - Ukrainian - service - yes - childprotect - Legal services for children (free legal aid)': getlocation,
        'Language - Ukrainian - service - yes - childprotect - Individual   Child Protection Services': getlocation,
        'Language - Ukrainian - service - yes - employment - Daycareforchildrenservices': getlocation,
        'Language - Ukrainian - service - yes - employment - Day care for elderly & people with disabilities': getlocation,
        'Language - Ukrainian - service - yes - employment - LanguageClasses': getlocation,
        'Language - Ukrainian - service - yes - employment - jobtrainprog': getlocation,
        'Language - Ukrainian - service - yes - employment - JobPlacementServices': getlocation,
        'Language - Ukrainian - service - yes - employment - Legal Support to access work': getlocation,
        'Language - Ukrainian - service - yes - healthcare - Maternal & newborn health': getlocation,
        'Language - Ukrainian - service - yes - healthcare - Pediatrics': getlocation,
        'Language - Ukrainian - service - yes - healthcare - MedicalClinics': getlocation,
        'Language - Ukrainian - service - yes - healthcare - Secondary  & tertiary Care': getlocation,
        'Language - Ukrainian - service - yes - healthcare - Health Support': getlocation,
        'Language - Ukrainian - service - yes - healthcare - Communicable diseases': getlocation,
        'Language - Ukrainian - service - yes - healthcare - Medical tests': getlocation,
        'Language - Ukrainian - service - yes - healthcare - Medicines': getlocation,
        'Language - Ukrainian - service - yes - healthcare - Primary care': getlocation,
        'Language - Ukrainian - service - yes - healthcare - Non communicable diseases': getlocation,
        'Language - Ukrainian - service - yes - healthcare - Sexual violence': getlocation,
        'Language - Ukrainian - service - yes - healthcare - Recovery': getlocation,
        'Language - Ukrainian - service - yes - healthcare - Hospitals': getlocation,
        'Language - Ukrainian - service - yes - healthcare - STI & HIV/AIDS': getlocation,
        'Language - Ukrainian - service - yes - mentalHealth - Group   counselling': getlocation,
        'Language - Ukrainian - service - yes - mentalHealth - Specialized Services': getlocation,
        'Language - Ukrainian - service - yes - mentalHealth - Psychiatrists': getlocation,
        'Language - Ukrainian - service - yes - mentalHealth - Support for children and youth': getlocation,
        'Language - Ukrainian - service - yes - mentalHealth - IndividualConsultations': getlocation,
        'Language - Ukrainian - service - yes - Disability-Specific   Services': getlocation,
        'Language - Ukrainian - service - yes - Violence   Support': getlocation,
        'Language - Ukrainian - service - yes - legalAssis - Refugee Legal Aid': getlocation,
        'Language - Ukrainian - service - yes - legalAssis - Individual Consultations': getlocation,
        'Language - Ukrainian - service - yes - legalAssis - Human Trafficking support': getlocation,
        'Language - Ukrainian - service - yes - legalAssis - Support with Documentation': getlocation,
        'Language - Ukrainian - service - yes - Community Centers/Services': getlocation,

        # 'Language - English - service - yes - other - fallback': get_service_name,
        # 'Language - English - service - yes - other - fallback': getlocation,
        'cities': get_city_name,
        'View Services': view_result,
        'View Services - yes': getlocation,
        'View Services - no': restart_convo,
        'View Services - no - no': thankyou_rating,
        'View Services - no - no - rating': convo_end,
    }

    agent.handle_request(intent_map)
    return jsonify(agent.response), 200

if __name__ == "__main__":
    app.run(debug=True,port=5000)
