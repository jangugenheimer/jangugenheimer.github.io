---
layout: default
title: Publications
---

# Publications

{% assign papers = site.data.publications | where: "type", "paper" %}
{% assign by_year = site.data.publications | group_by: "year" | sort: "name" | reverse %}
<p class="lead">{{ papers.size }} peer-reviewed papers and {{ site.data.publications | size | minus: papers.size }} posters, demos, workshops and other contributions, newest first. The full list is on <a href="{{ site.links.scholar }}" target="_blank" rel="noopener">Google Scholar</a>.</p>

<div class="pubviz" id="pubviz" hidden>
<div class="types" role="group" aria-label="Filter by type"></div>
<div class="venues" role="group" aria-label="Filter by venue"></div>
<div class="timeline" aria-label="Papers per year"></div>
<p class="viz-status" aria-live="polite"></p>
</div>

<nav class="years" aria-label="Jump to year">
{% for y in by_year %}<a href="#y{{ y.name }}">{{ y.name }}</a>{% endfor %}
</nav>

{% for y in by_year %}
<section class="year" id="y{{ y.name }}">
<h2 class="year-label">{{ y.name }}</h2>
<div class="pubs">
{% for p in y.items %}{% include publication.html pub=p %}{% endfor %}
</div>
</section>
{% endfor %}

<script src="{{ '/assets/js/publications.js' | relative_url }}" defer></script>
