---
# the default layout is 'page'
icon: fas fa-calendar-week
order: 4
---

<!-- See: [用GitHub-Pages搭建博客及Jekyll主题设置-海边捡点贝壳](https://xienotes.net/2020/04/25/github-pages-and-jekyll.html) -->


{% assign posts = site.posts | where: 'categories', 'weekly' %}

<ul>
  {% for post in posts %}
  <li>
  <span>{{ post.date | date: '%Y-%m-%d' }}</span>&nbsp;
  <a href="{{site.baseurl}}{{ post.url }}">{{ post.title }}</a>
  </li>
  {% endfor %}
</ul>
