---
layout: default
title: Publications
---

# Publications

<p class="lead">{{ site.data.publications | size }} peer-reviewed papers, newest first. A play symbol on an image means there is a video. The full list is on <a href="{{ site.links.scholar }}">Google Scholar</a>.</p>

{% assign by_year = site.data.publications | group_by: "year" | sort: "name" | reverse %}
{% for y in by_year %}
<section class="year">
<h2 class="year-label" id="y{{ y.name }}">{{ y.name }}</h2>
<div class="pubs">
{% for p in y.items %}{% include publication.html pub=p %}{% endfor %}
</div>
</section>
{% endfor %}
