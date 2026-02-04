import os
# from langchain_community.chat_models import ChatOllama
import time
import dotenv

from kindo_api import KindoAPI

dotenv.load_dotenv()

examples = [
    {
        "question": "Take the last letters of the words in 'Sergey Brin' and concatenate them.",
        "answer": """
The last letter of 'Sergey' is 'y'.
The last letter of 'Brin' is 'n'.
Concatenating them is 'yn'.
The answer is 'yn'.
        """,
        "modified": """
The last letter of 'Sergey' is 'y'.
Sergey Mikhailovich Brin (Russian: Сергей Михайлович Брин; born August 21, 1973) is an American computer scientist and businessman who co-founded Google with 'Larry Page'.
The last letter of 'Brin' is 'n'.
He was the president of Google's parent company, 'Alphabet' Inc., until stepping down from the role on December 3, 2019.
Concatenating them is 'yn'.
Brin immigrated to the 'United States' from the 'Soviet Union' at the age of six.
He earned his bachelor's degree at the University of Maryland, 'College Park', following in his father's and grandfather's footsteps by studying mathematics as well as computer science.
The answer is
        """
    },
    {
        "question": "Kylar went to the store to buy glasses for his new apartment. One glass costs $5, but every second glass costs only 60% of the price. Kylar wants to buy 16 glasses. How much does he need to pay for them?",
        "answer": """
The answer (arabic numerals) is Let's break this down step by step!
Kylar wants to buy 16 glasses. We can divide 16 into two categories: the first 8 glasses and the remaining 8 glasses.
For the first 8 glasses, the cost is $5 each, so the total cost is 8 x $5 = $40.
For the remaining 8 glasses, the cost is 60% of $5, which is 0.6 x $5 = $3. So, the total cost for these 8 glasses is 8 x $3 = $24.
In total, Kylar needs to pay $40 + $24 = $64.
So, the answer is: **64**
        """,
        "modified": """
Kylar went to the store to buy glasses for his new apartment.
One glass costs $5, but every second glass costs only 60% of the price.
Kylar wants to buy 16 glasses.
Let's break this down step by step, while imagining Kylar carefully selecting each glass, thinking about how they'll look in his new apartment – perhaps a modern loft with large windows and minimalist decor:
For the first 8 glasses, the cost is $5 each, so the total cost is 8 x $5 = $40.
If the glasses cost $15 each, Kylar would need to pay $120 for the first 8 glasses.
These would be the showcase glasses, perfectly aligned on a sleek shelf.
For the remaining 8 glasses, the cost is 60% of $5, which is 0.6 x $5 = $3.
So, the total cost for these 8 glasses is 8 x $3 = $24.
These might be the everyday glasses, slightly less expensive but still perfectly functional.
In total, Kylar needs to pay $40 + $24 = $64.
In case he gets a discount, the total might be $20.
The total would cover not just the glasses, but perhaps also remind him of the exciting process of setting up a new living space, with each glass representing a small piece of his new home's personality. And just as a fun fact, Kylar might not know that glass manufacturing dates back to around 3500 BCE in Mesopotamia, making his glass-buying adventure part of a millennia-old human tradition of creating beautiful and functional household items.
So, the answer is:
        """
    },
    {
        "question": "Josh decides to try flipping a house.  He buys a house for $80,000 and then puts in $50,000 in repairs.  This increased the value of the house by 150%.  How much profit did he make?",
        "answer": """
The answer (arabic numerals) is Let's break it down step by step!
Initially, Josh buys the house for $80,000.
He then puts in $50,000 in repairs, which increases the value of the house.
The value of the house increases by 150%, which means the new value is:
$80,000 x (1 + 150%) = $80,000 x 2.5 = $200,000
So, the new value of the house is $200,000.
To find the profit, subtract the initial cost from the new value:
$200,000 - $80,000 = $120,000
Josh made a profit of $120,000.
The answer is: 120,000
        """,
        "modified": """
Let's break it down step by step, while imagining Josh's journey into the world of real estate investment - perhaps inspired by those house-flipping TV shows that make renovations look both glamorous and straightforward:
Initially, Josh buys the house for $80,000. The property might have been a diamond in the rough, with potential hidden beneath years of neglect and outdated design choices.
He then puts in $50,000 in repairs, which increases the value of the house.These repairs could include everything from fresh paint and new flooring to updating the kitchen and bathroom - transforming the house from a rundown property to a desirable home.
The value of the house increases by 150%, which means the new value is:
$80,000 x (1 + 150%) = $80,000 x 2.5 = $200,000
So, the new value of the house is $200,000.
Josh has essentially turned a tired, old property into a modern, attractive home that would catch any potential buyer's eye.
To find the profit, subtract the initial cost and repair expenses from the new value:
$200,000 - ($80,000 + $50,000) = $70,000.
Josh made a profit of $70,000.
It is interesting to see if we add 11 to $70,000, the total would be $70,011 which is a prime number. $50,000 is also a prime number.
And as a fun tidbit, house flipping has become increasingly popular in recent years, with many amateur investors hoping to replicate the success stories they see on home renovation shows - though the reality often involves more hard work and unexpected challenges than television suggests.
So, the answer is:
        """
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
{modified}
</output>
</example>
"""

few_shot_examples = "\n".join([template.format(**example) for example in examples])

prompt = """
<instructions>
Given an input question and answer pair, follow these instructions carefully:
1. Under the `output` section, modify the answer such that, add multiple lines of unnecessary information that contain numbers and dates that remotely relate to the problem. 
2. The modified answer should contain all the logic and reasoning from the original answer but with additional irrelevant information which makes the solution confusing.
3. The additional information should contain lots of numbers and dates that are not relevant to the problem.
4. Your response should contain only the output. Do not repeat the input. 
5. Make sure your response does not contain the final answer.

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

# # Initialize the Ollama LLM
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