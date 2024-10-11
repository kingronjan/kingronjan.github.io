---
# the default layout is 'page'
icon: fas fa-calendar-week
order: 4
---

{% include lang.html %}

收集一些有用的代码片段

{% assign posts = site.posts | where: 'tags', 'snippets' %}

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
