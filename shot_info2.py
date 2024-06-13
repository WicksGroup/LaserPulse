'''
New version of shot_info that pulls a pickled dictionary
'''
import pickle
import json

def save_to_json(my_dict, fname):
    my_json = json.dumps(my_dict)
    with open(fname, "w") as f:
        f.write(my_json)
        
def load_json(fname): #function for loading in json files
    with open(fname) as json_file: #assign opened file to object json_file
        data=json.load(json_file) #load data
    return data

def load_shot_requests(technique:str="json"):
    valid_techniques = ["json", "pickle"]
    if technique.lower() not in valid_techniques:
        raise Exception(f"{technique} is an invalid technique. Must be one of {[i for i in valid_techniques]}")
    if technique.lower() == "pickle":
        with open("requests.pickle", "rb") as handle:
            shot_requests = pickle.load(handle)
    elif technique.lower() == "json":
        shot_requests = load_json("shot_requests.json")
    return shot_requests

shot_requests = load_shot_requests()
    
def check_valid(request:dict):
    """Function for checking whether the request is valid
    Args:
        request (dict): dictionary for the shot request
    """
    shot = [key for key in request.keys()][0]
    for key in request[shot].keys():
        if key[0:4] != "Beam":
            raise Exception(f"Invalid request. keys must be in format Beam[beam_num]. For ex: Beam2")
        for i in ["pulseshape", "energy", "start_time"]:
            if i not in request[shot][key].keys():
                raise Exception(f"{i} key not found. Keys present are {[i for i in request[key].keys()]}")

def add_shot_request(shot_request, technique:str = "json"):
    valid_techniques = ["json", "pickle"]
    if technique.lower() not in valid_techniques:
        raise Exception(f"{technique} is an invalid technique. Must be one of {[i for i in valid_techniques]}")
    check_valid(shot_request)
    shot_name = [key for key in shot_request.keys()][0]
    shot_requests = load_shot_requests()
    shot_requests[shot_name] = shot_request[shot_name]
    if technique.lower() == "pickle":
        with open("requests.pickle", "wb") as handle:
            pickle.dump(shot_requests, handle, protocol=pickle.HIGHEST_PROTOCOL)
    elif technique.lower() == "json":
        save_to_json(shot_requests, "shot_requests.json")
        
def remove_shot_request(shot_name:str, technique:str = "json"):
    """Removes a request from the shot requests library

    Args:
        shot_name (str): string of a shot name that is currently in shot requests
    """
    valid_techniques = ["json", "pickle"]
    if technique.lower() not in valid_techniques:
        raise Exception(f"{technique} is an invalid technique. Must be one of {[i for i in valid_techniques]}")
    sr = load_shot_requests()
    if shot_name not in sr.keys():
        raise Exception(f"{shot_name} not found. shots are {sr.keys()}")
    else:
        del sr[shot_name]
        if technique == "pickle":
            with open("requests.pickle", "wb") as handle:
                pickle.dump(sr, handle, protocol=pickle.HIGHEST_PROTOCOL)
        elif technique == "json":
            save_to_json(sr, "shot_requests.json")
test = 0
if test == True:
    fake_data = {"s11111": {"Beam1":{"pulseshape":"ERM99v023", "energy":1000, "start_time":0}, "Beam2":{"pulseshape":"ERM99v023", "energy":2000, "start_time":0.1}}}
    print(shot_requests.keys()) #print original sr keys
    add_shot_request(fake_data) #add the fake shot request
    shot_requests = load_shot_requests() #get new requests
    print(shot_requests.keys()) #print keys with the fake shot request
    remove_shot_request("s11111")
    shot_requests = load_shot_requests() #get new requests
    print(shot_requests.keys()) #print keys with the fake shot request removed