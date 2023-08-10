import openai
import json
import aiolimiter
import aiohttp
import asyncio
import environ
import os
import requests

from io import BytesIO

from datetime import datetime
from django.utils.text import slugify
from django.conf import settings


from .models import Article, Image

env = environ.Env(DEBUG=(bool, False))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

environ.Env.read_env(os.path.join(BASE_DIR, '.env'))


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


async def prompt_gpt(messages, functions=None, retries=0):
    if retries >= 10:
        functions = None

    for _ in range(10):
        try:
            if functions:
                completion = await openai.ChatCompletion.acreate(
                    model='gpt-3.5-turbo-16k',
                    messages=messages,
                    functions=functions
                )

                func = completion['choices'][0]['message'].get('function_call')

                if func and func['name'] not in apply_function:
                    messages.append({
                        'role': 'system',
                        'content': 'The function you called is not available.'
                    })

                    return await prompt_gpt(messages, functions, retries=retries + 1)

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
                        {"sub-heading":"The sub heading","keypoints":["Point 1","Point 2","Point 3","Point 4","Point 5",]},
                        {"sub-heading":"The sub heading","keypoints":["Point 1","Point 2","Point 3","Point 4","Point 5",]},
                        {"sub-heading":"The sub heading","keypoints":["Point 1","Point 2","Point 3","Point 4","Point 5",]},
                        {"sub-heading":"The sub heading","keypoints":["Point 1","Point 2","Point 3","Point 4","Point 5",]}
                    ], "title":"The title for the complete blog post"
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
{guidelines}.
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

    return content


async def generate_image_prompt(content: str):
    messages = [
        {
            'role': 'user',
            'content': f"""
{content}\n\nGenerate the description for an image from the above data.
The description should only be of 3 lines maximum. It will be given to DALL-E 2 to generate the image."""
        }
    ]

    completion = await prompt_gpt(messages)
    return completion_to_content(completion)


def prompt_image_generation(prompt: str):
    for _ in range(5):
        try:
            image = openai.Image.create(
                prompt=prompt,
                n=1,
                size='512x512'
            )

            return image
        except:
            pass


def generate_image(prompt: str, fname: str):
    res = prompt_image_generation(prompt)

    if not res:
        return

    res = requests.get(res['data'][0]['url'])

    if res.status_code != 200:
        for _ in range(5):
            try:
                res = requests.get(res['data'][0]['url'])
                if res.status_code == 200:
                    break
            except Exception as e:
                print(e)

    fname += '.png'
    image = Image(name=fname)
    image.image.save(fname, BytesIO(res.content))
    image.save()

    return image


async def summarize(content: str):
    messages = [
        {
            'role': 'system',
            'content': """
You are given the scraped text of web pages. You clean the text and respond with the main content discussed on the page.
Donot respond any of the features of the webpage or the navigation of the webpage, rather return the content discussed in the article.
"""
        },
        {
            'role': 'user',
            'content': f"""
{content}

Clean the content given in the above article.
"""
        }
    ]

    return completion_to_content(await prompt_gpt(messages))


async def summarize(content: str):
    messages = [
        {
            'role': 'user',
            'content': f"""
{content}

Summarise the above article in 4 - 5 sentences.
"""
        }
    ]

    return completion_to_content(await prompt_gpt(messages))


async def rewrite(content: str):
    messages = [
        {
            'role': 'user',
            'content': f"""
{content}

Don't repeat yourself, rewrite this and correct any coherency mistakes. Also don't remove the HTML while rewriting.
Feel free to use HTML and CSS to make it look good. This will be used as a section of a larger webpage, so don't define
the head, body and such tags. Those will be already made for the page, you will only write content for the text content."""
        }
    ]

    return completion_to_content(await prompt_gpt(messages))


async def generate(guidelines: str):
    try:
        overview = json.loads(completion_to_content(await generate_article_overview(guidelines)))
        content = await generate_article(overview, guidelines)

        body = ""

        for section in content:
            body += f"""<div class="section">{section}</div>"""

        body = await rewrite(body)

        slug: str = slugify(overview.get('title'))
        slug = slug if slug else slugify(body[:100])

        try:
            article = await Article.objects.acreate(slug=slug)
        except Exception as e:
            print(e)
            return

        article.title = overview.get('title')

        article.body = body
        article.summary = await summarize(body)

        await article.asave()

        return article
    except Exception as e:
        print(e)
        return
