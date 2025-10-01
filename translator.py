# T-araVLN

import re
import os
import json


def extract(text):
   thought_match = re.search(r'<thought>(.*?)</thought>', text, re.DOTALL | re.IGNORECASE)
   after_match = re.search(r'<after_instruction>(.*?)</after_instruction>', text, re.DOTALL | re.IGNORECASE)
   thought = thought_match.group(1) if thought_match else ''
   after_instruction = after_match.group(1) if after_match else ''
   return thought, after_instruction


def clean(content):
   content = content.strip()
   content = re.sub(r'\s*\n\s*', ' ', content)
   content = re.sub(r'^[^a-zA-Z]+', '', content)
   if not re.match(r'.*[\.\!\?]$', content):
      content += '.'
   return content


def translator(before_instruction, model, client):

   system_prompt = """
   You are an expert in Vision-and-Language Navigation (VLN) for agricultural robots. Your mission is to translate the instruction from casual spoken-language style containing complete semantics to formal written-language style retaining only essential semantics, thereby making the instruction easier to understand for downstream VLN decision-making models. To accomplish this mission, please follow five principles: 
   1. Inessential Removal Principle: Delete all the inessential words which have no direct connection to navigation, such as 'good morning'.
   2. Errors Revision Principle: Revise all the speaking errors, such as 'left rotate to face it... no, right rotate' should be revised to 'right rotate to face it'.
   3. High-Low Separation Principle: Distinguish between the high-level introduction (if present) and the low-level orders, then clearly separate them using an explicit delimiter phrase, such as 'you need to navigate to the water station to get some water so that we can water plants. right rotate to...' can be revised to 'your task is to navigate to the water station. To achieve this task, you need to right rotate to...'.
   4. Representational Rotation Principle: Polish the end condition for rotation (if present) from abstract description to representational description, such as 'left rotate to face the green sprayer' can be revised to 'keep left rotating to face the green sprayer until it is in your horizontal center'.
   5. Representational Movement Principle: Polish the end condition for moving forward (if present) from abstract description to representational description, such as 'stop when you reach the blue tractor' can be revised to 'stop when you are very close to the blue tractor, at that time it should occupy all your camera view'.

   Input Format: 
   <before_instruction> {the instruction before translation} </before_instruction>

   Output Format: 
   <thought> {your reasoning process} </thought>
   <after_instruction> {the instruction after translation} </after_instruction>

   Additional Rules:
   - Express the content in `<after_instruction>` in natural language; avoid using enumerations such as '1.' or '2.'.
   - Ensure all output tags are properly aligned and well-formed: every opening tag (e.g., <thought>) must have a corresponding closing tag (e.g., </thought>), with no missing or mismatched tags.
   """

   user_prompt = f'<before_instruction> {before_instruction} </before_instruction>'

   completion = client.chat.completions.create(
      model=model,
      stream=False,
      messages=[
         {"role": "system", "content": system_prompt},
         {"role": "user", "content": user_prompt}
      ]
   )

   thought, after_instruction = extract(completion.choices[0].message.content)
   thought = clean(thought)
   after_instruction = clean(after_instruction)

   print('Translate successfully.')
   print()
   print(f'Thought: {thought}')
   print()
   print(f'Before: {before_instruction}')
   print()
   print(f'After: {after_instruction}')
   print()

   return thought, after_instruction


def save_after_instruction(after_instruction_path, before_instruction, after_instruction, place, id, translator_thought):

   entry = {
      "episode_id": f"{place}_{id}",
      "before_instruction": before_instruction,
      "after_instruction": after_instruction,
      "translator_thought": translator_thought
   }
   
   os.makedirs(os.path.dirname(after_instruction_path), exist_ok=True)
   
   if os.path.exists(after_instruction_path):
      with open(after_instruction_path, "r", encoding="utf-8") as f:
         try:
               data = json.load(f)
         except json.JSONDecodeError:
               data = []
   else:
      data = []
   
   data.append(entry)
   
   with open(after_instruction_path, "w", encoding="utf-8") as f:
      json.dump(data, f, ensure_ascii=False, indent=2)
