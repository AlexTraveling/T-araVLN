from openai import OpenAI
import argparse
import os
import json
import time

from STL import STL
from decide import decide
from evaluate import evaluate
from translator import translator, save_after_instruction


def check_label_format(label_path):
   valid_actions = {"[FORWARD]", "[LEFT ROTATE]", "[RIGHT ROTATE]", "[STOP]", "[WAIT]"}
   with open(label_path, "r") as f:
      labels = json.load(f)
   for i in range(len(labels)):
      entry = labels[i]
      if entry["action"] not in valid_actions:
         print(f"[Error] Action NO. {i} is invalid: {entry['action']}")
         return False
      if i < len(labels) - 1:
         end_time = round(labels[i]["time_range"][1], 3)
         next_start_time = round(labels[i + 1]["time_range"][0], 3)
         if end_time != next_start_time:
            print(f"[Error] Time step {i} and {i+1} are not connected: {end_time} ≠ {next_start_time}")
            return False
   print("[Info] The format of label is correct.")
   return True


def get_api_key(place):
   api_key_house = {
      "farm": "replace_by_your_api_key_1",
      "greenhouse": "replace_by_your_api_key_2",
      "forest": "replace_by_your_api_key_3",
      "mountain": "replace_by_your_api_key_4",
      "garden": "replace_by_your_api_key_5",
      "village": "replace_by_your_api_key_6"
   }
   if place not in api_key_house:
      raise ValueError(f"[Error] Unknown scene: {place}")
   else:
      api_key = api_key_house[place]
      return api_key


if __name__ == '__main__':

   parser = argparse.ArgumentParser()
   parser.add_argument("--place", type=str, required=True, help="Input the agricultural scene classification.")
   args = parser.parse_args()
   place = args.place

   exp = 'qualitative_experiment'
   translator_model = 'gpt-4.1'
   model = "gpt-4.1-mini"
   id_range = list(range(1, 10))
   
   print(f'scene: {place}')
   print(f'id_range: {id_range}')

   client = OpenAI(api_key=get_api_key(place), base_url="replace_by_your_api")
   
   for id in id_range:
      dir_path = f"runs/{exp}/{place}_{id}"
      if os.path.exists(dir_path) and os.listdir(dir_path):
         print(f"episode {place}_{id} is already been run.")
         time.sleep(0.1)
         continue
      os.makedirs(dir_path, exist_ok=True)

      label_path = f"dataset/{place}_{id}/label.json"
      if check_label_format(label_path) == False:
         print('label error')
      else:
         print(f'--- {exp} ---')

         with open(f"dataset/{place}_{id}/info.json", 'r') as f:
            before_instruction = json.load(f)['instruction']
         translator_thought, after_instruction = translator(before_instruction, translator_model, client)
         after_instruction_path = f"runs/{exp}/{place}_{id}/after_instruction.json"
         save_after_instruction(after_instruction_path, before_instruction, after_instruction, place, id, translator_thought)
         time.sleep(0.1)

         STL(model, exp, place, id, after_instruction, client)
         time.sleep(0.1)

         decide(model, exp, place, id, client)
         time.sleep(0.1)

         evaluate(exp, place, id)
         time.sleep(0.1)

         print(f'--- end ---')
