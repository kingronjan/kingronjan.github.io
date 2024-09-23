---
# the default layout is 'page'
icon: fas fa-calendar-week
order: 4
---

<!-- 

See: [用GitHub-Pages搭建博客及Jekyll主题设置-海边捡点贝壳](https://xienotes.net/2020/04/25/github-pages-and-jekyll.html) 
Also: https://github.com/cotes2020/jekyll-theme-chirpy/blob/master/_layouts/category.html

-->

{% include lang.html %}

{% assign posts = site.posts | where: 'categories', 'weekly' %}

<div id="page-category">
  <ul class="content ps-0">
    {% for post in posts %}
      <li class="d-flex justify-content-between px-md-3">
        <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
        <span class="dash flex-grow-1"></span>
        {% include datetime.html date=post.date class='text-muted small text-nowrap' lang=lang %}
      </li>
    {% endfor %}
  </ul>
</div>