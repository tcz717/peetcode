# pylint: skip-file
import re
import json
from time import sleep

from SCons.Script import *

from peetcode import Leetcode, readall, writeall, LANGS, Project

EnsurePythonVersion(3, 6)


# Functions
def generate_code(target, source, env):
    pro = env['PROJECT']
    code = source[0].get_text_contents()
    code = lc.playgroundcode(
        pro.id, pro.lang, pro.url, code)
    writeall(str(target[0]), code)


def extract_code(target, source, env):
    pro = env['PROJECT']
    code = source[0].get_text_contents()
    uploadzone = re.search(
        r'{}\s*(.+)\s*{}'.format(pro.lang.beginmark, pro.lang.endmark), code, re.S)
    writeall(str(target[0]), uploadzone[1] if uploadzone else code)


def submit_code(target, source, env):
    pro = env['PROJECT']
    subid = lc.submit(id=pro.id, lang=pro.lang,
                      code=source[0].get_text_contents())
    if not subid:
        return "Submit fail"

    result = None
    for i in range(int(env['MAXSUBRETRY'])):
        result = lc.check(subid)
        if result:
            break

        print(env.subst('Waiting result %d/$MAXSUBRETRY') % (i + 1))
        sleep(1)

    if not result:
        return 'Timeout'

    print('Test result:', result['status_msg'])
    print('Passed: {}/{}'.format(
        result['total_correct'], result['total_testcases']))

    status = result['status_code']
    if status == 10:
        return
    elif status == 11:
        print('For input: {}, Expected: {}, Got: {}'.format(
            result['input'], result['expected_output'], result['code_output']))
        writeall(os.path.join(pro.testdir, str(subid) + '.in'),
                 result['input'])
        writeall(os.path.join(pro.testdir, str(subid) + '.exp'),
                 result['expected_output'])
    else:
        for k, v in result.items():
            print('{} = {}'.format(k, v))
    return result['status_msg']


def create_project(target, source, env):
    proj: Project = env['PROJECT']
    pro = lc.getproblem(proj.url)

    dirpath = proj.dir

    if os.path.exists(dirpath):
        return "problem already exists!"

    os.mkdir(dirpath, 0o777)

    defaultcode = next((
        lang['defaultCode'] for lang in json.loads(pro['data']['question']['codeDefinition'])
        if lang['value'] == proj.lang.name
    ))
    content = pro['data']['question']['content']
    content = re.sub(r'(\r\n)+', '\n', content)
    defaultcode = proj.lang.beginmark + '\n' + \
        re.sub(r'(\r\n)+', '\n', defaultcode) + '\n' + proj.lang.endmark
    template = env.File('template${PROJECT.lang.ext}', 'templates')
    print(template)
    if template.exists():
        print('applying template')
        defaultcode = re.sub(r"\$DEFAULTCODE", defaultcode,
                             template.get_text_contents())

    writeall(proj.srcpath, defaultcode)
    writeall(os.path.join(dirpath, 'README.html'), content)

    os.mkdir(proj.testdir, 0o777)
    writeall(os.path.join(proj.testdir, 'sample.in'),
             pro['data']['question']['sampleTestCase'])


# Builders
test = Builder(action=Action('time -f "Time: %Us" $PROGRAM < $SOURCE | tee $TARGET | echo "Output: $$(cat -)"',
                             'Testing $SOURCE ...'),
               suffix='.out', src_suffix='.in')
diff = Builder(action=Action('diff -w $SOURCE ${SOURCE.base}.out && echo Accepted',
                             'Comparing $SOURCE and ${SOURCE.base}.out ...'),
               suffix='.diff', src_suffix='.exp')

# Actions
login = Action(lambda target, source, env: lc.login(
    env['user'], env['pass']) and None, "Login Leetcode with username = $user")
submit = Action(submit_code, "Submitting $SOURCE ...")
extract = Action(extract_code, "Extracting upload zone in $SOURCE ..")

lc = Leetcode()

# Variables
vars = Variables()
vars.Add('user', 'The username of your Leetcode account')
vars.Add('pass', 'The password of your Leetcode account')
vars.Add(EnumVariable('lang', 'The prject language', 'cpp',
                      allowed_values=LANGS.keys()))
vars.Add('id', 'The problem id', 'PROBLEMID')
vars.Add('MAXSUBRETRY', 'The maxinum submit retry times', 10)

# Environment
env = Environment(CXXFLAGS='--std=c++11 -g', variables=vars)
env.Append(BUILDERS={
    'Test': test,
    'Diff': diff
})
Help(vars.GenerateHelpText(env))

# Cache Update
meta = env.Command('lc.json', None, lambda target, source, env: lc.update())
env.AlwaysBuild(meta)
env.Alias('update', meta)

# Login
cookies = env.Command('.cookies', None, login)
Alias('login', cookies)
AlwaysBuild(Alias('login'))

# Problems
for p in lc.allproblems.values():
    proj = env.Clone(PROJECT=Project(p, env['lang']))
    create = proj.Command('${PROJECT.id}-create', None, Action(
        create_project, 'Creating new ${PROJECT.lang} project "${PROJECT.title}" ...'))
    proj.Pseudo(create)

# Projects
for p in lc.allprojects:
    proj = env.Clone(PROJECT=p, id=p.id, lang=p.lang)
    src = proj.File(p.srcpath)

    # Generate compilable code
    gen = proj.Command(p.genpath, src, Action(
        generate_code, "Generating compilable code for $SOURCE .."))
    proj.Precious(gen)
    proj.Alias('$id-$lang-gen', gen)
    proj.Alias('$id-gen', gen)

    # Extract uploadable code
    upload = proj.Command(p.uploadpath, src, extract)
    proj.Alias('$id-$lang-upload', upload)
    proj.Alias('$id-upload'.format(p.id), upload)

    program = proj.Program(p.execpath, gen)
    proj.Alias('$id-$lang', program)
    proj.Alias('$id'.format(p.id), program)

    testdir = proj.Dir('test', p.dir)
    testin = testdir.glob('*.in')
    testexp = testdir.glob('*.exp')
    testout = [proj.Test(t, PROGRAM=program) for t in testin]
    testdiff = [proj.Diff(t) for t in testexp]
    proj.AlwaysBuild(testout)
    proj.Depends(testout, program)
    proj.Depends(testdiff, testout)
    proj.Pseudo(testdiff)
    proj.Alias('$id-$lang-test', [testout, testdiff])
    proj.Alias('$id-test', [testout, testdiff])

    proj_submit = proj.Command('$id-$lang-submit', upload, submit)
    proj.Depends(proj_submit, cookies)
    proj.Pseudo(proj_submit)

Alias('create', env.Alias('$id-create'))
Alias('test', env.Alias('$id-$lang-test'))
Alias('submit', env.Alias('$id-$lang-submit'))
Default(env.Alias('$id-$lang'))
