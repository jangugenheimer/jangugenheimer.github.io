---
layout: default
title: Home
---

<section class="hero" markdown="1">
<div class="hero-text" markdown="1">

<p class="eyebrow">Human-Computer Interaction · TU Darmstadt</p>

<h1>Jan Gugenheimer</h1>

<p class="role">Assistant Professor (W2, tenure track), Department of Computer Science</p>

I lead the Human-Computer Interaction group at [TU Darmstadt](https://www.informatik.tu-darmstadt.de). My research lies at the intersection of **Extended Reality**, **Human-AI Interaction**, and the **safety, security and ethics** of these technologies. I study how AI-driven immersive systems can alter what people perceive, remember and decide, and I build systems and safeguards that keep this influence beneficial and under the user's control.

<p class="contact">
<a class="btn" href="{{ site.links.scholar }}" target="_blank" rel="noopener"><svg class="icon" aria-hidden="true"><use href="#i-cap"/></svg>Google Scholar</a>
{% if site.links.linkedin != "" %}<a class="btn" href="{{ site.links.linkedin }}" target="_blank" rel="noopener"><svg class="icon" aria-hidden="true"><use href="#i-ext"/></svg>LinkedIn</a>{% endif %}
{% if site.links.youtube != "" %}<a class="btn" href="{{ site.links.youtube }}" target="_blank" rel="noopener"><svg class="icon" aria-hidden="true"><use href="#i-play"/></svg>YouTube</a>{% endif %}
</p>
</div>
<div class="hero-photo"><img class="portrait" src="/assets/img/jan.jpg" alt="Jan Gugenheimer"></div>
</section>

## Research

<div class="pillars" markdown="1">
<div class="pillar" markdown="1">

### Perceptual manipulations and computational deception

Techniques that exploit the limits of human perception, such as redirected walking, can be misused to steer users without their awareness. We study these manipulations in XR, from false memories through source confusion to generative AI that produces deceptive designs on its own.

<div class="minis">
{% assign keys = "tseng2022dark,bonnail2023memory,krau2025create,wombacher2025switchar" | split: "," %}
{% for k in keys %}{% assign paper = site.data.publications | where: "key", k | first %}{% include pub-mini.html pub=paper %}{% endfor %}
</div>

</div>
<div class="pillar" markdown="1">

### Engineering interaction for AI-driven XR

We build hardware and software for interaction, feedback and collaboration in AR and VR, from bringing non-HMD users into shared VR (ShareVR, FaceDisplay) to real-time generative models running on headset passthrough.

<div class="minis">
{% assign keys = "mei2026shadar,gruenefeld2022vrception,gugenheimer2018facedisplay,gugenheimer2017sharevr" | split: "," %}
{% for k in keys %}{% assign paper = site.data.publications | where: "key", k | first %}{% include pub-mini.html pub=paper %}{% endfor %}
</div>

</div>
</div>

{% assign papers = site.data.publications | where: "type", "paper" %}
<p class="more"><a class="btn" href="/publications/">All {{ papers.size }} publications<svg class="icon" aria-hidden="true"><use href="#i-arrow"/></svg></a></p>
