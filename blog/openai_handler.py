import openai
import json
import aiolimiter
import aiohttp
import asyncio
import environ
import os

from datetime import datetime
from django.utils.text import slugify


from .models import Article

env = environ.Env(DEBUG=(bool, False))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

openai.api_key = env.get_value('OPENAI_API_KEY')

limiter = aiolimiter.AsyncLimiter(60, 1)


def completion_to_content(x) -> str:
    return x['choices'][0]['message'].get('content')


async def wiki_get(session: aiohttp.ClientSession, title: str):
    if limiter:
        await limiter.acquire()
    async with session.get(f'https://en.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&exintro=&explaintext=&titles={title}') as response:
        if response.status != 200:
            return ''

        pages = (await response.json())['query']['pages']

        text = pages[[key for key in pages][0]]['extract']

    return text


async def wiki_search(args) -> str | list[str]:
    topic = args.get('topic')

    if not topic:
        raise Exception(
            "Invalid arguments to wiki_search got {} expected {'topic':'The actual topic'}".format(args))

    try:
        async with aiohttp.ClientSession() as session:
            if limiter:
                await limiter.acquire()
            async with session.get(f'https://en.wikipedia.org/w/api.php?format=json&action=query&list=search&srsearch={topic}&format=json') as response:
                titles = (await response.json())['query']['search']

            text = await asyncio.gather(*[wiki_get(session, item['title']) for item in titles])

        return text

    except Exception as e:
        print('Error', e)
        return 'No information found'


async def current_date(*args, **kwargs):
    return datetime.now().today()


async def prompt_gpt(messages, functions=None):
    for _ in range(10):
        try:
            if functions:
                completion = await openai.ChatCompletion.acreate(
                    model='gpt-3.5-turbo-16k',
                    messages=messages,
                    functions=functions
                )
            else:
                completion = await openai.ChatCompletion.acreate(
                    model='gpt-3.5-turbo-16k',
                    messages=messages
                )

            return completion
        except Exception as e:
            print(e)

    return None


apply_function = {
    'wiki_search': wiki_search,
    'current_date': current_date
}

functions = [
    {
        "name": "wiki_search",
        "description": "Get the summarised articles from the Wikipedia.",
        "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic to get the relevant information, e.g. Astrology",
                    }
                },
            "required": ["topic"],
        },
    },
    {
        "name": "current_date",
        "description": "Get the current date.",
        "parameters": {
            "type": 'object',
            "properties": {},
            "required": []
        },
    }
]


async def generate_article_overview(content: str):
    messages = [
        {
            'role': 'system',
            'content': "You are a skilled writer. You generate articles about given topics. You are provided access to Wikipedia to get any relevant information that you deem necessary. Generate the content you are asked and return it in the required format."
        },
        {
            'role': 'user',
            'content': """
                Generate key points and topics discussed in a blog. The blog will have several subheadings and key-points for each subheading.
                \n""" + content + """\n\n
                The format of the output should be like this:

                <format>
                {
                    "sub-headings": [
                        {
                            "sub-heading":"The sub heading",
                            "keypoints":["Point 1","Point 2","Point 3","Point 4","Point 5",]
                        },
                        {
                            "sub-heading":"The sub heading",
                            "keypoints":["Point 1","Point 2","Point 3","Point 4","Point 5",]
                        },
                        {
                            "sub-heading":"The sub heading",
                            "keypoints":["Point 1","Point 2","Point 3","Point 4","Point 5",]
                        },
                        {
                            "sub-heading":"The sub heading",
                            "keypoints":["Point 1","Point 2","Point 3","Point 4","Point 5",]
                        }
                    ]
                    "title":"The title for the complete blog post"
                }
                </format>
            """
        }
    ]

    global functions
    completion = await prompt_gpt(messages, functions)

    if not completion:
        raise Exception('Null returned from prompt-gpt')

    while completion['choices'][0]['message'].get('function_call'):
        func_call = completion['choices'][0]['message'].get('function_call')

        func = apply_function[func_call['name']]
        args = json.loads(func_call['arguments'])

        res = await func(args)

        messages.append({
            'role': 'function',
            'name': func_call['name'],
            'content': f'{res}'
        })

        completion = await prompt_gpt(messages, functions)

    try:
        json.loads(completion_to_content(completion))
    except:
        messages += [
            {
                'role': 'assistant',
                'content': completion_to_content(completion)
            },
            {
                'role': 'user',
                'content': "Your answer does not follow the JSON format. Rewrite it and remove any repetitions."
            }
        ]

        completion = await prompt_gpt(messages)

    return completion


async def generate_section(guidelines: str, past: str, current):
    messages = [
        *[{
            'role': 'assistant',
            'content': item
        } for item in past],
        {
            'role': 'user',
            'content': f"""Here are the guidelines for the entire blog post, not this section alone:
{guidelines}.\nNo need to add headings and only write the paragraphs for the article.
The headings will be given through the overview of the section you will see following this message.
Write some content about this section: {current}. Feel free to use HTML to make the text appropriate and better lookhin.
Don't use h1 tags as they are for higher level headings, you can use h2 and below headings.
"""
        }
    ]

    completion = await prompt_gpt(messages, functions)

    while completion['choices'][0]['message'].get('function_call'):
        func_call = completion['choices'][0]['message'].get('function_call')

        func = apply_function[func_call['name']]
        args = json.loads(func_call['arguments'])

        res = await func(args)

        messages.append({
            'role': 'function',
            'name': func_call['name'],
            'content': f'{res}'
        })

        completion = await prompt_gpt(messages, functions)

    return completion

async def generate_article(overview, guidelines):
    content = []
    for section in overview.get('sub-headings'):
        content.append(completion_to_content(await generate_section(guidelines, content, str(section))))

    content = [{
        'text':text
    } for idx, text in enumerate(content)]

    return content


async def generate(guidelines: str):
    try:
        overview = json.loads(completion_to_content(await generate_article_overview(guidelines)))

        content = await generate_article(overview, guidelines)

        slug: str = slugify(overview.get('title'))

        try:
            article = await Article.objects.acreate(slug=slug)
        except:
            return

        article.title = overview.get('title')
        article.body = json.dumps(content)

        await article.asave()

        return article
    except:
        return
