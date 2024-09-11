import argparse
import html
import os
import os.path
import re
import sys
import time
from pathlib import Path

import requests
from prettymd import format

try:
    import toolconf as settings
except ImportError:
    raise FileExistsError('Settings file does not exists, create one like toolconf.py.template')


def get_filename(title):
    title = title.replace('|', ' ')
    title = title.replace('\\', '')
    title = re.sub(r'\s+', '-', title)
    return title


def main():
    parser = argparse.ArgumentParser('post-tools')
    parser.add_argument('title', nargs='*', help='title for post')
    parser.add_argument('-d --dir-path', dest='dir_path', default='_posts', help='which dir for place the new post')
    parser.add_argument('-f --file', dest='file', default=None,
                        help="if specified, will read the file's content as post content")
    
    subparser = parser.add_subparsers()
    asset_parser = subparser.add_parser('assets')
    asset_parser.add_argument('-c --clean', dest='clean', help='clean unused assets files.', action='store_true')

    args = parser.parse_args(sys.argv[1:])
    if args.clean:
        return remove_unused_assets()

    title = args.title
    if len(title) > 1:
        raise ValueError('support one title only')

    if not title:
        if not args.file:
            raise ValueError('no file and no title specified')

        title = os.path.split(args.file)[-1]
        title, filetype = title.rsplit('.', maxsplit=1)

    else:
        title = title[0]
        filetype = 'md'

    categories = args.dir_path.split('_posts')[-1]
    categories = categories.strip(os.sep)
    categories = categories.split(os.sep)
    categories = ', '.join(categories)

    tags = categories.lower()

    date = time.strftime('%Y-%m-%d %H:%M %z')
    filename = get_filename(title)
    filename = date.split()[0] + '-' + filename + '.' + filetype

    base_dir = Path(__file__).parent.absolute()
    filepath = base_dir / args.dir_path / filename

    # XXX: suport template/config file for each folder.
    with open(filepath, 'w', encoding='utf8') as f:
        f.write('---\n')
        f.write('layout: post\n')
        f.write(f'title: "{title}"\n')
        f.write(f'date: {date}\n')
        f.write(f'categories: [{categories}]\n')
        f.write(f'tags: [{tags}]\n')
        f.write('---\n\n')

        if args.file:
            with open(args.file, 'r', encoding='utf8') as rf:
                content = format(rf.read(), style='code')
                f.write(content)

    print(f'post created at: {filepath}')


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


def remove_unused_assets():
    # 加载文件并拼接为字符串
    counter = {}

    for dirpath, _, filenames in os.walk(settings.BASE_DIR / 'assets'):
        if dirpath.endswith('favicons'):
            continue

        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            filepath = filepath.split('assets', maxsplit=1)[-1]
            filepath = filepath.replace('\\', '/')
            counter[filepath] = 0

    print('searching files usage: \n', '\n'.join(counter))

    find_usages('_posts', counter)
    find_usages('_tabs', counter)
    find_usages('_config.yml', counter)

    print('usage counts:', '\n'.join(f'{path=}, {count=}' for path, count in counter.items()))

    for path, count in counter.items():
        if count:
            continue
        
        path = settings.BASE_DIR / 'assets' / path.strip('/')
        print('removing unused file: ', path)
        os.remove(path)


def find_usages(dirname, counter):
    def count(filepath):
        with open(filepath, 'r', encoding='utf8') as f:
            content = f.read()
            for path in counter:
                counter[path] += content.count(path)

    dirpath = settings.BASE_DIR / dirname
    if not dirpath.exists():
        raise FileNotFoundError(f'file {dirname} not exists in {settings.BASE_DIR}')

    print('finding usage in', dirpath)

    if dirpath.is_file():
        return count(dirpath)

    for dirpath, _, filenames in os.walk(dirpath):
        for filename in filenames:
            if not filename.endswith('.md'):
                continue

            filepath = os.path.join(dirpath, filename)
            count(filepath)


if __name__ == '__main__':
    remove_unused_assets()
