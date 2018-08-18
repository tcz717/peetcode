#!/usr/bin/python3

import argparse
import io
import json
import os
import pickle
import re
from glob import glob
from typing import List, Union, Dict

import requests


def writeall(path, txt):
    with open(path, 'w') as f:
        f.write(txt)


def readall(path):
    with open(path, 'r') as f:
        return f.read()


class Language:
    begin_upload_zone = 'BEGIN UPLOAD ZONE'
    end_upload_zone = 'END UPLOAD ZONE'

    def __init__(self, name: str, ext: str, comment: str):
        self.name = name
        self.ext = ext
        self.comment = comment

    @property
    def beginmark(self):
        return "{} {}".format(self.comment, self.begin_upload_zone)

    @property
    def endmark(self):
        return "{} {}".format(self.comment, self.end_upload_zone)

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def withext(self, path):
        return path + self.ext


LANGS: Dict[str, Language] = {
    lang.name: lang for lang in [
        Language(name='c', ext='.c', comment='//'),
        Language(name='cpp', ext='.cpp', comment='//'),
        Language(name='csharp', ext='.cs', comment='//'),
        Language(name='python', ext='.py', comment='#'),
    ]
}


class lazy:
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls):
        val = self.func(instance)
        setattr(instance, self.func.__name__, val)
        return val


class Project:
    def __init__(self, entry: dict, lang: Union[Language, str]):
        assert(lang.isprintable)
        assert(entry)
        self.entry = entry
        self.lang = lang if isinstance(lang, Language) else LANGS[lang]

    @property
    def slug(self):
        return self.entry['stat']['question__title_slug']

    @property
    def title(self):
        return self.entry['stat']['question__title']

    @property
    def id(self):
        return self.entry['stat']['question_id']

    @property
    def dir(self):
        return "{}-{}-{}".format(self.id, self.lang, self.slug)

    @property
    def testdir(self):
        return os.path.join(self.dir, 'test')

    @property
    def srcpath(self):
        return os.path.join(self.dir, 'solution' + self.lang.ext)

    @property
    def genpath(self):
        return os.path.join(self.dir, 'solution.gen' + self.lang.ext)

    @property
    def uploadpath(self):
        return os.path.join(self.dir, 'solution.upload' + self.lang.ext)

    @property
    def execpath(self):
        return os.path.join(self.dir, 'solution')

    @property
    def url(self):
        return 'https://leetcode.com/problems/{}/description/'.format(self.slug)


class Leetcode:
    origin = 'https://leetcode.com'

    def __init__(self):
        self._all: dict = None

    @property
    def all(self):
        if self._all:
            return self._all

        if os.path.exists('lc.json'):
            self._all = json.loads(readall('lc.json'))
        else:
            self.update()
        return self._all

    @lazy
    def allprojects(self)->List[Project]:
        projs = glob(r"*-*-*")
        for p in projs:
            i, lang, slug = re.match(r"(\d+)-(\w+)-([\w-]+)", p).groups()
            entry = self.allproblems[int(i)]
            assert(slug == entry['stat']['question__title_slug'])
            yield Project(entry, lang)

    @lazy
    def allproblems(self):
        assert(self.all != None)
        return {p['stat']['question_id']: p for p in self.all['stat_status_pairs']}

    @lazy
    def idlist(self) -> List[int]:
        return (p['stat']['question_id'] for p in self.all['stat_status_pairs'])

    @lazy
    def session(self) -> requests.Session:
        session = requests.session()
        session.headers.update({
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
            'origin': self.origin
        })

        if os.path.exists('.cookies'):
            with open('.cookies', 'rb') as f:
                session.cookies.update(pickle.load(f))

        session.get(self.origin)
        session.headers.update({
            'x-csrftoken': session.cookies.get('csrftoken')
        })
        return session

    def getproblem(self, url: str) -> dict:
        if url.isnumeric():
            pid = int(url)
            url = 'https://leetcode.com/problems/{}/description'.format(
                self.allproblems[pid]['stat']['question__title_slug'])

        r = self.session.post('https://leetcode.com/graphql', headers={'referer': url}, json={
            'query':
            """
                query getQuestionDetail($titleSlug: String!) {
                    question(titleSlug: $titleSlug) {
                        questionId
                        questionTitleSlug
                        content
                        stats
                        codeDefinition
                        sampleTestCase
                        enableRunCode
                        metaData
                        translatedContent
                    }
                }
            """,
            'variables': {'titleSlug': re.match(r'https://leetcode.com/problems/([\w-]+)/.*', url).group(1)},
            'operationName': 'getQuestionDetail'
        })
        return r.json()

    def playgroundcode(self, id: int, lang: str, url: str, code='')->str:
        r: requests.Response = self.session.post(
            'https://leetcode.com/playground/new/empty',
            headers={'referer': url},
            data={
                'csrfmiddlewaretoken': self.session.cookies.get('csrftoken'),
                'code': code,
                'question': id,
                'testcase': '',
                'lang': lang
            })
        html = r.text
        return re.search(r"\W+code: '(.*)',\n", html)[1].encode().decode('unicode_escape')

    def update(self):
        r: requests.Response = self.session.get(
            'https://leetcode.com/api/problems/all/',
            headers={'referer': 'https://leetcode.com/problemset/all/'}
        )
        self._all = r.json()
        writeall('lc.json', json.dumps(
            self._all, indent=4, ensure_ascii=False))

    def getproject(self, id)->Project:
        if id not in self.allproblems:
            print('Problem id {} not exists'.format(id))
            exit(-1)

        projs = glob(r"{}-*-*".format(id))
        if len(projs) > 1:
            print('multiple projects')

        lang, slug = re.match(
            r"{}-(\w+)-([\w-]+)".format(id), projs[0]).groups()

        entry = self.allproblems[id]
        assert(slug == entry['stat']['question__title_slug'])

        return Project(entry, lang)

    def login(self, user: str, password: str, file='.cookies'):
        url = 'https://leetcode.com/accounts/login/'
        self.session.get(url)
        r = self.session.post(
            url,
            headers={'referer': url},
            data={
                'csrfmiddlewaretoken': self.session.cookies.get('csrftoken'),
                'login': user,
                'password': password,
            })

        if 'LEETCODE_SESSION' not in self.session.cookies:
            print('Login Fail:', r.status_code)
            return False

        with open(file, 'wb') as f:
            pickle.dump(self.session.cookies, f)

        return True

    def submit(self, id: int, code: str, lang: Language):
        pro = self.allproblems[id]
        slug = pro['stat']['question__title_slug']
        assert(lang)
        r = self.session.post(
            'https://leetcode.com/problems/{}/submit/'.format(slug),
            headers={
                'referer': 'https://leetcode.com/problems/{}/description/'.format(slug)},
            json={
                'lang':        lang.name,
                'question_id': id,
                'test_mode':   False,
                'typed_code':  code,
                'judge_type': 'large'
            }
        )
        return r.json()['submission_id']

    def check(self, submission_id)->dict:
        result = self.session.get('https://leetcode.com/submissions/detail/{}/check/'.format(submission_id),
                                  headers={'referer': 'https://leetcode.com/'}).json()
        if result['state'] == 'SUCCESS':
            return result
        else:
            return None