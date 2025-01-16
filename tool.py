import argparse
import hashlib
import html
import os
import os.path
import re
import logging
import subprocess
import sys
import uuid
from datetime import datetime

from fnmatch import fnmatch

import frontmatter

try:
    import toolconf as settings
except ImportError:
    raise FileExistsError('Settings file does not exists, create one like toolconf.py.template')

logger = logging.getLogger('tool')


def get_filename(title):
    title = title.replace('|', ' ')
    title = title.replace('\\', '')
    title = re.sub(r'\s+', '-', title)
    return title


class CnBlogOperator(object):

    def __init__(self):
        self.exists_posts = set()
        self.home = settings.CNBLOG_HOME_URL
        self.cookies = settings.CNBLOG_COOKIES
        self.headers = settings.CNBLOG_HEADERS
        self.post_dir = settings.CNBLOG_POST_DIR

    def load_exists(self):
        base_dir = settings.BASE_DIR / '_posts'
        if not os.path.exists(base_dir):
            return

        for dirpath, _, filenames in os.walk(base_dir):
            for filename in filenames:
                with open(os.path.join(dirpath, filename), 'r', encoding='utf-8') as f:
                    result = re.search(r'cnblogid: (\d+)', f.read())
                    if result:
                        self.exists_posts.add(result.groups()[0])

    def exists(self, post_id):
        if not self.exists_posts:
            self.load_exists()
            if not self.exists_posts:
                self.exists_posts.add(None)

        return post_id in self.exists_posts

    def get(self, url, **kwargs):
        import requests

        kwargs.setdefault('cookies', self.cookies)
        kwargs.setdefault('headers', self.headers)
        return requests.get(url, **kwargs)

    def parse(self, url=None):
        from lxml import etree

        if url is not None:
            response = self.get(url)
        else:
            response = self.get(self.home)

        root = etree.HTML(response.text)
        for div in root.xpath('//div[@role="article"]'):
            a = div.xpath('.//a[contains(@class, "postTitle2")]')[0]
            title = a.xpath('.//span/text()')[0].strip()
            link = a.xpath('./@href')[0]
            link = link.replace('.html', '')
            post_id = link.rsplit('/', 1)[-1]

            date = div.xpath('.//div[@class="postDesc"]/text()')[0]
            date = date.split('@')[-1].strip().rsplit(maxsplit=1)[0]

            print(f'title={title}, link={link}, post_id={post_id}, date={date}')

            if self.exists(post_id):
                print('该文章已存在，跳过')
                continue

            c_url = f'{self.home}/ajax/post-accessories?postId={post_id}'
            resp = self.get(c_url)

            categories = resp.json()['categoriesTags']
            categories = etree.HTML(categories)

            category = categories.xpath('.//div[@id="BlogPostCategory"]/a/text()')
            if category:
                category = category[0]
                category = category.split(' / ')

            tags = categories.xpath('.//div[@id="EntryTag"]//a/text()')

            print(f'category={category}, tags={tags}')

            resp = self.get(link + '.md')
            content = resp.text.replace('<br/>', '')
            content = html.unescape(content)

            self.post_to_jekyll(title, date, category, tags, post_id, content)

        try:
            next_page = root.xpath('.//a[contains(text(), "下一页")]/@href')[0]
            self.parse(next_page)
        except IndexError:
            pass

    def post_to_jekyll(self, title, date, category, tags, post_id, content):
        if not os.path.exists(self.post_dir):
            os.makedirs(self.post_dir)

        if category:
            category = ', '.join(category)
        else:
            category = ''

        if tags:
            tags = ', '.join(tags)
        else:
            tags = ''

        tags = tags.lower()

        pure_date = date.split()[0]
        filename = pure_date + '-' + get_filename(title) + '.md'

        # Escape spacial chars.
        title = '"%s"' % title

        with open(os.path.join(self.post_dir, filename), 'w', encoding='utf-8') as f:
            post = settings.CNBLOG_POST_TEMPLATE % {'title': title, 'date': date, 'category': category, 'tags': tags,
                                                    'content': content, 'cnblogid': post_id}
            f.write(post)

        print(f'File {filename} saved')


def remove_unused_assets(args):
    if not args.clean:
        return print('skip clean without -c specified.')

    # 加载文件并拼接为字符串
    counter = {}

    for dirpath, _, filenames in os.walk(settings.BASE_DIR / 'assets'):
        if dirpath.endswith(('favicons', 'css')):
            continue

        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            filepath = filepath.split('assets', maxsplit=1)[-1]
            filepath = filepath.replace('\\', '/')
            counter[filepath] = 0

    print('searching files usage: \n', '\n'.join(counter))

    for filepath, content in read_posts():
        for path in counter:
            counter[path] += content.count(path)

    print('usage counts:', '\n'.join(f'{path=}, {count=}' for path, count in counter.items()))

    for path, count in counter.items():
        if count:
            continue
        
        path = settings.BASE_DIR / 'assets' / path.strip('/')
        print('removing unused file: ', path)
        os.remove(path)


def read_posts(config=True):

    def read_dir(name):
        dirpath = settings.BASE_DIR / name
        for dirpath, _, filenames in os.walk(dirpath):
            for filename in filenames:
                if not filename.endswith('.md'):
                    continue
                filepath = os.path.join(dirpath, filename)
                with open(filepath, 'r', encoding='utf8') as f:
                    yield filepath, f.read()

    yield from read_dir('_posts')
    yield from read_dir('_tabs')

    if config:    
        configfile = settings.BASE_DIR / '_config.yml'
        with open(configfile, 'r', encoding='utf8') as f:
            yield configfile, f.read()


def check_vertical_line(args):
    if not args.vertical_line:
        return print('skip check without -v specified')

    pattern = re.compile(r'\[.*?(?<!\\)\|.*?\]\(.+?\)')

    for filename, content in read_posts():
        links = pattern.findall(content)
        if not links:
            continue

        for link in links:
            escaped_link = link.replace(r'\|', '|')
            escaped_link = escaped_link.replace('|', r'\|')
            content = content.replace(link, escaped_link)

        with open(filename, 'w', encoding='utf8') as f:
            f.write(content)
        
        print('Vertical line was escaped from ', filename)


class Counter(object):

    def __init__(self):
        self.nsynced = 0
        self.nskipped = 0
        self.nchanged = 0

    def incr_synced(self, num=1):
        self.nsynced += num

    def incr_skipped(self, num=1):
        self.nskipped += num

    def incr_changed(self, num=1):
        self.nchanged += num

    @property
    def total(self):
        return self.nskipped + self.nchanged


class PostParser(object):

    def __init__(self, filepath, rootpath, indexes):
        self.filepath = filepath
        _, self.filename = os.path.split(self.filepath)

        self.rootpath = rootpath
        self.indexes = indexes

        if not rootpath.endswith(os.sep):
            rootpath += os.sep

        self.dirpath = os.path.dirname(filepath).replace(rootpath, '')
        self.postid = None
        self.publish = False
        self.post = None

    def parse(self):
        self.post = frontmatter.load(self.filepath)
        self.publish = self.post.get('publish', True)
        if not self.publish:
            return logger.info('Skipped post %s cause publish disabled', self.filepath)

        attr_makes = {
            'id': self.make_postid,
            'layout': self.make_layout,
            'date': self.make_date,
            'title': self.make_title,
            'categories': self.make_categories,
            'tags': self.make_tags,
        }

        for attr, make in attr_makes.items():
            if attr not in self.post:
                value = make()
                logger.debug('generate default value for %s: %s = %s', self.filepath, attr, value)
                self.post[attr] = value

        self.postid = self.post['id']

    @staticmethod
    def make_postid():
        return str(uuid.uuid4())

    @staticmethod
    def make_layout():
        return 'post'

    def make_date(self):
        stat = os.stat(self.filepath)
        date = datetime.fromtimestamp(stat.st_mtime)
        return date.strftime('%Y-%m-%d %H:%M +0800')

    def make_title(self):
        logger.debug('generating title by %s', self.filename)

        if self.filename.endswith('.md'):
            filename = self.filename[:-3]
        else:
            filename = self.filename

        return filename

    def make_categories(self):
        filepath, _ = os.path.split(self.filepath)
        path = filepath.replace(self.rootpath, '')
        logger.debug('generating categories by path: %s', path)
        categories = []
        for x in path.split(os.sep):
            x = x.strip()
            if not x:
                continue
            categories.append(x)
        return categories

    def make_tags(self):
        return self.make_categories()

    def digest(self):
        with open(self.filepath, 'rb') as f:
            md5 = hashlib.md5()
            md5.update(str(self.filepath).encode('utf8'))
            md5.update(f.read())
            return md5.hexdigest()

    def sync(self):
        self.parse()
        raw_digest = self.digest()

        if self.postid in self.indexes:
            target_file = self.indexes[self.postid]
            if ' ' in target_file:
                digest, target_file = target_file.split(maxsplit=1)
            else:
                digest = None

            if digest and digest == raw_digest:
                logger.debug('file %s no changes (digest: %s)', self.filepath, digest)
                frontmatter.dump(self.post, self.filepath, encoding='utf-8')
                logger.debug('file %s metadata flushed', self.filepath)
                return False

        else:
            target_file = None

        if not self.publish and target_file:
            logger.info('remove published file: %s (cause publish disabled)', target_file)
            os.remove(target_file)
            self.indexes.pop(self.postid)
            return True

        prefix = self.post['date'].split()[0] + '-'
        filename = self.get_filename()
        expect_target_file = os.path.join(str(settings.POST_DIR), str(self.dirpath), prefix + filename)

        if target_file != expect_target_file:
            logger.debug('file %s name changed to %s', target_file, expect_target_file)
            os.remove(target_file)
            target_file = expect_target_file

        os.makedirs(os.path.dirname(target_file), exist_ok=True)
        frontmatter.dump(self.post, target_file, encoding='utf-8')

        relative_filepath = target_file.replace(str(settings.BASE_DIR), '')
        relative_filepath = relative_filepath.strip(os.sep)
        self.indexes[self.postid] = '%s %s' % (raw_digest, relative_filepath)
        logger.debug('file %s synced to %s, id: %s', self.filepath, target_file, self.postid)

        frontmatter.dump(self.post, self.filepath, encoding='utf-8')
        logger.debug('file %s metadata flushed', self.filepath)

        return True

    def get_filename(self):
        title = self.filename.replace('|', ' ')
        title = title.replace('\\', '')
        title = re.sub(r'\s+', '-', title)
        return title


def sync_posts(args):
    indexes = {}
    counter = Counter()

    if not os.path.exists(settings.INDEX_FILE):
        logger.warning('index file %s does not exist', settings.INDEX_FILE)

    else:
        with open(settings.INDEX_FILE, 'r', encoding='utf8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                postid, path = line.split(maxsplit=1)
                indexes[postid] = path

        logger.info('%s indexes loaded from file %s', len(indexes), settings.INDEX_FILE)

    for dirpath, dirnames, filenames in os.walk(args.dirpath):
        for filename in filenames:
            if not filename.endswith('.md'):
                counter.incr_skipped()
                continue

            fullpath = os.path.join(dirpath, filename)

            skipped = False
            for pat in settings.IGNORE_FILES:
                if fnmatch(fullpath, pat):
                    logger.debug(f'Ignore file {fullpath} which matches {pat}')
                    skipped = True
                    break

            if skipped:
                counter.incr_skipped()
                continue

            parser = PostParser(fullpath, args.dirpath, indexes)
            if parser.sync():
                counter.incr_synced()
                counter.incr_changed()
            else:
                counter.incr_skipped()

    logger.info('Done, %s file processed, %s file changed, %s file synced, %s file skipped.' % (counter.total, counter.nchanged, counter.nsynced, counter.nskipped))

    if counter.nchanged:
        with open(settings.INDEX_FILE, 'w', encoding='utf8') as f:
            f.write('\n'.join(f'{k} {v}' for k, v in indexes.items()))
            logger.info('%s indexes flushed to %s', len(indexes), settings.INDEX_FILE)
    else:
        logger.info('No index change detected.')

    if not args.git:
        return

    max_retries = 1
    retried = 0
    failed = False

    while retried <= max_retries:
        files = get_unstaged_files()
        if not files:
            failed = True
            break

        os.system('git add ' + ' '.join(files))
        if os.system('git commit -m "%s"' % args.message):
            failed = True
        else:
            break

        retried += 1

    if failed:
        sys.exit(1)

    os.system('git push')


def get_unstaged_files():
    logger.info('Fetching changed files...')
    result = subprocess.check_output('git status', shell=True, text=True)
    result = re.search(r'Changes not staged for commit:\n(.*?)(no changes|$)', result, re.S)
    if not result:
        return logger.info('No changes added to commit')

    result = result.groups()[0]
    files = []
    for file in result.split('\n'):
        file = file.strip()
        if not file or file.startswith('(use'):
            continue

        if file.startswith('Untracked files:'):
            continue

        logger.info('find unstaged file: %s', file)
        try:
            opr, file = file.split(maxsplit=1)
        except ValueError:
            pass
        files.append(file)

    logger.info('%s files found', len(files))
    if not files:
        return

    return files


def init_posts(args):
    indexes = []

    for dirpath, dirnames, filenames in os.walk('_posts'):
        dirs = dirpath.split(os.sep)[1:]
        target_path = os.path.join(args.dirpath, *dirs)
        os.makedirs(target_path, exist_ok=True)

        for filename in filenames:
            if not filename.endswith('.md'):
                continue

            filepath = os.path.join(dirpath, filename)
            post = frontmatter.load(filepath)
            if 'id' not in post:
                post['id'] = str(uuid.uuid4())

            target_file = os.path.join(str(target_path), re.sub(r'^\d{4}-\d{2}-\d{2}-', '', filename))
            frontmatter.dump(post, target_file, encoding='utf8')
            logger.info('file %s successfully write to %s, id: %s', filepath, target_file, post['id'])
            indexes.append('%s %s' % (post['id'], filepath))

    with open(settings.INDEX_FILE, 'w', encoding='utf8') as f:
        f.write('\n'.join(indexes))

    logger.info('index file %s flushed', settings.INDEX_FILE)


def main():
    parser = argparse.ArgumentParser('post-tools')
    parser.add_argument('title', nargs='*', help='title for post')
    parser.add_argument('-d --dir-path', dest='dir_path', default='_posts', help='which dir for place the new post')
    parser.add_argument('-f --file', dest='file', default=None,
                        help="if specified, will read the file's content as post content")
    parser.add_argument('-l --level', dest='level', default=None,
                        help="log level")
    
    subparser = parser.add_subparsers(dest='subcmd')
    asset_parser = subparser.add_parser('assets')
    asset_parser.add_argument('-c --clean', dest='clean', help='clean unused assets files.', action='store_true')
    asset_parser.set_defaults(func=remove_unused_assets)

    check_parser = subparser.add_parser('check')
    check_parser.add_argument('-v --vertical-line', dest='vertical_line', action='store_true', help='escape vertical line in links, aviod render error')
    check_parser.set_defaults(func=check_vertical_line)

    init = subparser.add_parser('init')
    init.add_argument('-d --dirpath', dest='dirpath', default=r'C:\Users\lineu\OneDrive\blogs')
    init.set_defaults(func=init_posts)

    sync = subparser.add_parser('sync')
    sync.add_argument('-d --dirpath', dest='dirpath', default=r'C:\Users\lineu\OneDrive\blogs')
    sync.add_argument('-g --git', dest='git', action='store_true')
    sync.add_argument('-m --message', dest='message', default='update posts.')
    sync.set_defaults(func=sync_posts)

    args = parser.parse_args()

    logconf = settings.LOG.copy()
    if args.level:
        logconf.update({'level': args.level})
    logging.basicConfig(**logconf)

    if args.subcmd:
        args.func(args)
    else:
        raise NotImplementedError('require subcommand.')


if __name__ == '__main__':
    main()
