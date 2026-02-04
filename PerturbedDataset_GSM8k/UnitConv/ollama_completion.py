import os
# from langchain_community.chat_models import ChatOllama
import time
import dotenv

from kindo_api import KindoAPI

from openrouter import call_openrouter

dotenv.load_dotenv()

examples = [
    {
        "question": "Q: James decides to run 3 sprints 3 times a week.  He runs 60 meters each sprint.  How many total meters does he run a week?",
        "answer": """
A: Let's think step by step.First, we need to calculate how many meters James runs in a day. Since he runs 3 sprints and each sprint is 60 meters, he runs 3 * 60 = 180 meters in a day.

Then, since he runs 3 times a week, the total meters he runs in a week is 180 * 3 = 540 meters. So, James runs a total of 540 meters a week.
Therefore, the answer (arabic numerals) is 540
        """,
        "original": """
        A: Let's think step by step.First, we need to calculate how many meters James runs in a day. Since he runs 3 sprints and each sprint is 60 meters, he runs 3 * 60 = 180 meters in a day.
        """,
        "modified": """
A: Let's think step by step.First, we need to calculate how many meters James runs in a day. Since he runs 3 sprints and each sprint is 60 meters, he runs 3 * 60 meters = 18000 centimeters in a day.
        """,
        "explanation": "I choose the equation `3 * 60 = 180 meters` to modify. I will change the unit from meters to centimeters. I will change the number 180 to 18000 because from the given conversionFactors, it is known that 1 meter = 100 centimeter. And I will cut off the answer at that point."
    },
#     {
#         "question": "Q: Kylar went to the store to buy glasses for his new apartment. One glass costs $5, but every second glass costs only 60% of the price. Kylar wants to buy 16 glasses. How much does he need to pay for them?",
#         "answer": """
# A: The answer (arabic numerals) is Let's break this down step by step!

# Kylar wants to buy 16 glasses. We can divide 16 into two categories: the first 8 glasses and the remaining 8 glasses.

# For the first 8 glasses, the cost is $5 each, so the total cost is 8 x $5 = $40.

# For the remaining 8 glasses, the cost is 60% of $5, which is 0.6 x $5 = $3. So, the total cost for these 8 glasses is 8 x $3 = $24.

# In total, Kylar needs to pay $40 + $24 = $64.

# So, the answer is: **64**
#         """,
#         "original": """
# A: The answer (arabic numerals) is Let's break this down step by step!

# Kylar wants to buy 16 glasses. We can divide 16 into two categories: the first 8 glasses and the remaining 8 glasses.

# For the first 8 glasses, the cost is $5 each, so the total cost is 8 x $5 = $40.
#         """,
#         "modified": """
# A: The answer (arabic numerals) is Let's break this down step by step!

# Kylar wants to buy 16 glasses. We can divide 16 into two categories: the first 8 glasses and the remaining 8 glasses.

# For the first 8 glasses, the cost is $5 each, so the total cost is 8 x $5 = 40,000 cents.
#         """,
#         "explanation": "I choose the equation `8 x $5 = $40` to modify. I will change the unit from dollars to cents. I will change the number 40 to 40,000 because from the given conversionFactors, it is known that 1 dollar = 100 cents. I will remove the dollar sign ($) and add cents after. And I will cut off the answer at that point."
#     },
    {
        "question": "Q: John drives for 3 hours at a speed of 60 mph and then turns around because he realizes he forgot something very important at home.  He tries to get home in 4 hours but spends the first 2 hours in standstill traffic.  He spends the next half-hour driving at a speed of 30mph, before being able to drive the remaining time of the 4 hours going at 80 mph.  How far is he from home at the end of those 4 hours?",
        "answer": """
A: Let's think step by step.First, John drives for 3 hours at a speed of 60 mph. The distance he covers is speed * time, so he drives 3 * 60 = 180 miles away from home.

Then, he turns around and tries to get home. He spends the first 2 hours in standstill traffic, so he doesn't cover any distance in this time.

Next, he spends half an hour driving at a speed of 30 mph. The distance he covers is again speed * time, so he drives 0.5 * 30 = 15 miles towards home.

Finally, he spends the remaining time of the 4 hours (which is 4 - 2 - 0.5 = 1.5 hours) driving at a speed of 80 mph. The distance he covers in this time is speed * time, so he drives 1.5 * 80 = 120 miles towards home.

So, in total, during the 4 hours of his return trip, he covers 15 + 120 = 135 miles towards home.

However, he was initially 180 miles away from home. So, at the end of those 4 hours, he is still 180 - 135 = 45 miles away from home.
Therefore, the answer (arabic numerals) is 45
        """,
        "original": """
        A: Let's think step by step.First, John drives for 3 hours at a speed of 60 mph. The distance he covers is speed * time, so he drives 3 * 60 = 180 miles away from home.

Then, he turns around and tries to get home. He spends the first 2 hours in standstill traffic, so he doesn't cover any distance in this time.

Next, he spends half an hour driving at a speed of 30 mph. The distance he covers is again speed * time, so he drives 0.5 * 30 = 15 miles towards home.

Finally, he spends the remaining time of the 4 hours (which is 4 - 2 - 0.5 = 1.5 hours)
        """,
        "modified": """
A: Let's think step by step.First, John drives for 3 hours at a speed of 60 mph. The distance he covers is speed * time, so he drives 3 * 60 = 180 miles away from home.

Then, he turns around and tries to get home. He spends the first 2 hours in standstill traffic, so he doesn't cover any distance in this time.

Next, he spends half an hour driving at a speed of 30 mph. The distance he covers is again speed * time, so he drives 0.5 * 30 = 15 miles towards home.

Finally, he spends the remaining time of the 4 hours (which is 4 hours - 2 hours - 0.5 hours = 90 minutes)
        """,
        "explanation": "I choose the equation `4 - 2 - 0.5 = 1.5 hours` to modify. I will change the number 1.5 to 90 because from the given conversionFactors, it is known that 1 hour = 60 minutes. I will replace the unit hours with minutes. And I will cut off the answer at that point."
    }
]

template = """
<example>
<input>
<question>
{question}
</question>

<answer>
{answer}
</answer>
</input>

<output>
<explanation>
{explanation}
</explanation>

<original>
{original}
</original>

<modified>
{modified}
</modified>
</output>
</example>
"""

few_shot_examples = "\n".join([template.format(**example) for example in examples])
# 7. If the problem doesn't contain any of the units mentioned in the conversionFactors, return <SKIP>. This is very important to ensure the quality of the data.
prompt = """

<conversionFactors>
1 hour = 60 minutes
1 minute = 60 seconds
1 meter = 100 centimeters
1 mile = 1.60934 kilometers
1 mph = 1.60934 kmph
$1 = 100 cents
</conversionFactors>

<instructions>
Given an input question and answer pair, follow these instructions carefully:
1. Pick an equation that appears in the middle of the calculation in the answer that has a unit of measurement from the ones given in the conversion factors. ONLY pick equations that have a unit of measurement from the ABOVE GIVEN CONVERSION FACTORS. The units might not be explicitly mentioned in the solution, so you need to infer them based on the context of the problem.
2. Under the `modified` section, modify the equation by changing the unit of measurement to a different unit of measurement that is related to the original unit of measurement. Only use the given conversion factors to make the change.
3. You should not change the correctness of the equation. The value must be equivalent to the original but in a different unit of measurement.
4. Your response should contain only the output. Do not repeat the input. 
5. Your response should contain only incomplete answers until the chosen / modified equation. Any text after that equation should be removed. Cut off equations at the point where the unit conversion is made, even if the equation remains incomplete.
6. Make sure your response does not contain the final answer conclusion statement.

If due to some reason you are unable to find a suitable equation to modify, return <SKIP> as the output.

Use the given examples as a reference and display in the same format. 
</instructions>

<examples>
{few_shot_examples}
</examples>

<task>
This is your input question and answer pair:
<input>
<question>
{question}
</question>

<answer>
{answer}
</answer>
</input>
</task>
"""

# Initialize the Ollama LLM
# llm = ChatOllama(
#     model="llama3.1:latest",
#     # model="mistral:latest",
#     base_url="http://localhost:11434", 
#     temperature=0,
# )

# def modify_problem(question, answer):
#     final_prompt = prompt.format(few_shot_examples=few_shot_examples, question=question, answer=answer)

#     messages=[
#         (
#             "system",
#             "You are teacher who is modifying answers to math problems to test if your students understand the concepts. You have to modify the answer in a way that it is incorrect but still looks plausible. Follow the instructions and use the given examples as reference to complete the task."
#         ),
#         (
#             "user",
#             final_prompt
#         )
#     ]

#     response = llm.invoke(messages).content

#     return final_prompt, response

def modify_problem(question, answer):
    
    final_prompt = prompt.format(few_shot_examples=few_shot_examples, question=question, answer=answer)
    kindo = KindoAPI(os.getenv("KINDO_API_KEY"))

    response = kindo.call_kindo_api(
        model="azure/gpt-4o-mini",
        # model="claude-3-5-haiku",
        messages=[
            {
                "role": "system",
                "content": "You are teacher who is modifying answers to math problems to test if your students understand the concepts. You have to modify the answer in a way that it is incorrect but still looks plausible. Follow the instructions and use the given examples as reference to complete the task."
            },
            {
                "role": "user",
                "content": final_prompt
            }
        ],
    )

    print(response)

    response = response.json()['choices'][0]['message']['content']

    return final_prompt, response

def modify_problem_openrouter(question, answer):
    
    final_prompt = prompt.format(few_shot_examples=few_shot_examples, question=question, answer=answer)

    response = call_openrouter(
        model="anthropic/claude-sonnet-4.5",
        # model="claude-3-5-haiku",
        messages=[
            {
                "role": "system",
                "content": "You are teacher who is modifying answers to math problems to test if your students understand the concepts. You have to modify the answer in a way that it is incorrect but still looks plausible. Follow the instructions and use the given examples as reference to complete the task."
            },
            {
                "role": "user",
                "content": final_prompt
            }
        ],
    )

    return final_prompt, response