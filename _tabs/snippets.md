---
# the default layout is 'page'
icon: fas fa-code
order: 4
---

<!-- 

See: [用GitHub-Pages搭建博客及Jekyll主题设置-海边捡点贝壳](https://xienotes.net/2020/04/25/github-pages-and-jekyll.html) 
Also: https://github.com/cotes2020/jekyll-theme-chirpy/blob/master/_layouts/category.html

-->

{% include lang.html %}


收集一些有用的代码片段

{% assign posts = site.posts | where: 'categories', 'snippets' %}

<div id="page-category">
  <ul class="content ps-0">
    {% for post in posts %}
      <li class="d-flex justify-content-between px-md-3">
        <a href="{{ post.url | relative_url }}">{{ post.categories[0] }} | {{ post.title }}</a>
        <span class="flex-grow-1"></span>

      </li>
    {% endfor %}
  </ul>
</div>