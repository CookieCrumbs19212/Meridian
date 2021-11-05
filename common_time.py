# The cross_timezone_coordinator is restricted to finding a common timeframe within a 48hr period.

import re
import sys
from datetime import datetime, timedelta
import requests

# File where the API key is stored.
API_KEY_LOCATION = 'API_KEY.txt'
API_KEY = '' # API key for Abstract API (https://www.abstractapi.com/).

'''
NOTE: We need a date to assign our datetime object as we are create 'aware' datetime objects.
      Hence, regardless of the actual dates of the constraints, we use the current date in the system.
'''
# Datetime format.
dt_format = '%Y-%m-%d %H:%M:%S'
date_today = datetime.now().strftime('%Y-%m-%d')

# Stores the startTimes of each limit in GMT/UTC time.
start_times = []

# Stores the endTimes of each limit in GMT/UTC time.
end_times = []

# Variable to keep count of the number of constraints.
constraint_count = 0

# Method to load the API key from a text file.
def load_API_KEY():
    global API_KEY
    with open(API_KEY_LOCATION) as f:
        API_KEY = f.readline()

def convertToUTCOffsetZero(BASE_LOCATION, BASE_DATETIME_OBJ):
    TARGET_LOCATION = "Greenwich, United Kingdom"
    BASE_DATETIME = BASE_DATETIME_OBJ.strftime(dt_format)

    # Sending API request
    try:
        response = requests.get(f"https://timezone.abstractapi.com/v1/convert_time/?api_key={API_KEY}&base_location={BASE_LOCATION}&base_datetime={BASE_DATETIME}&target_location={TARGET_LOCATION}")
    except Exception as e:
        print(f"Abstract API Request failed. This may be caused due to an invalid location input or incorrect request format.\n")
        print(e)

    # Checking status code.
    if response.status_code <= 299:
        print(f"API Time Request completed with status code: {response.status_code}.\n")
    else:
        print(f"API Time Request failed with status code: {response.status_code}.\n\
            This may be caused due to an invalid location input.\n")

    # Converting response to json and getting 'datetime' value and returning it as a datetime object.
    return datetime.strptime(response.json()['target_location']['datetime'], dt_format)


def add(location, start_time_str, end_time_str):
    global constraint_count,start_times,end_times

    # Adding the colon in the time strings. 0900 -> 09:00
    start_datetime_object = datetime.strptime(f'{date_today} {start_time_str[0:2]}:{start_time_str[2:]}:00', dt_format)
    end_datetime_object = datetime.strptime(f'{date_today} {end_time_str[0:2]}:{end_time_str[2:]}:00', dt_format)

    # Adding the startTime as a datetime object.
    start_times.append(convertToUTCOffsetZero(location, start_datetime_object))

    # Checking if endTime is less than startTime (this means that the endTime is in the next day).
    if start_datetime_object < end_datetime_object :
        end_times.append(convertToUTCOffsetZero(location, end_datetime_object))
    else:
        end_times.append(convertToUTCOffsetZero(location, end_datetime_object + timedelta(days=1)))
   
    # Incrementing limit_count.
    constraint_count += 1

def clear():
    global constraint_count,start_times,end_times
    start_times.clear()
    end_times.clear()
    constraint_count = 0

def run():
    global start_times,end_times

    op_startTime = start_times[0]
    op_endTime = end_times[0]

    # Finding the latest start time.
    for item in start_times:
        if op_startTime > item:
            op_startTime = item

    # Finding the earliest end time.
    for item in end_times:
        if op_endTime < item:
            op_endTime = item    

    # Printing the result
    if op_startTime < op_endTime:
        common_time_frame = f'from {op_startTime.strftime("%H:%M")} to {op_endTime.strftime("%H:%M")}'
        delta = op_endTime - op_startTime
        difference = divmod(delta.days*1440 + (delta.seconds)/60, 60)
        duration = f'{int(difference[0])} hours and {int(difference[1])} minutes'
        print(f'\nThere is a common time frame {common_time_frame} ({duration})\n')
    else:
        print("\nNo common time frame for the set limits.\n")

def vis():
    # Keeps count of how many times the reference datetime object is incremented.
    increment_counter = 0

    for n in range(len(start_times)):
        # Creating a reference datetime which the other datetime objects will be measured against.
        reference_datetime = datetime.strptime(f'{date_today} 00:00:00', dt_format)
        increment_counter = 0
        output = ''
        while reference_datetime < start_times[n]:
            output += '|'
            # Incrementing by 30 mins.
            reference_datetime += timedelta(minutes = 30)
            increment_counter+=1
        while reference_datetime < end_times[n]:
            output += '#'
            # Incrementing by 30 mins.
            reference_datetime += timedelta(minutes = 30)
            increment_counter+=1
        while increment_counter < 98:
            output += '|'
            # Incrementing by 30 mins.
            reference_datetime += timedelta(minutes = 30)
            increment_counter+=1
        
        print(f'{output}\n')

def validateTime(time):
    return (len(time) == 4 and int(time[0:2]) <= 23 and int(time[2:]) <= 59)

def main():
    # Loading the API key from the txt file.
    load_API_KEY()

    print('\n\n\nRunning Cross Timezone Coordinator...\n\
        Commands: add   - add a new constraint\n\
                  run   - run the script and get the common time frame\n\
                  clear - clear all the constraits\n\
                  vis   - visualize the constraints\n\
                  quit  - quit Cross Timezone Coordinator\n')

    while True:
        user_command = input('command: ')

        if 'add' in user_command:
            location = input('\nLocation: ')

            while(True):
                start_time = input('\nStart time (HHMM): ')
                if validateTime(start_time):
                    break
                else:
                    print('\nInvalid start time input.\n')

            while(True):
                end_time = input('\nEnd time (HHMM): ')
                if validateTime(end_time):
                    break
                else:
                    print('\nInvalid end time input.\n')
            
            # Adding a new constraint
            add(location, start_time, end_time)

        elif 'clear' in user_command:
            clear()
            print('All constraints have been cleared.')

        elif user_command == 'vis':
            if constraint_count > 1:
                vis()
            else:
                print('\nYou need at least 2 constraints to visualize.')
    
        elif user_command == 'run':
            if constraint_count > 1:
                run()
            else:
                print('\nYou need at least 2 constraints to run.')
    
        elif user_command == 'quit':
            print('\n Quiting...')
            sys.exit()

        else:
            print('\nInvalid command.\n')

# Running script.
main()
