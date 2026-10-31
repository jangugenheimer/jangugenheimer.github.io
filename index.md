---
layout: default
title: Home
---

<section class="intro" markdown="1">
<img class="portrait" src="/assets/img/jan.jpg" alt="Jan Gugenheimer">
<div class="intro-text" markdown="1">

<p class="role">Assistant Professor (W2, tenure track) · Human-Computer Interaction<br>Department of Computer Science, TU Darmstadt</p>

I lead the [Human-Computer Interaction group](/group/) at [TU Darmstadt](https://www.informatik.tu-darmstadt.de). My research lies at the intersection of **Extended Reality**, **Human-AI Interaction**, and the **safety, security and ethics** of these technologies. I study how AI-driven immersive systems can alter what people perceive, remember and decide, and I build systems and safeguards that keep this influence beneficial and under the user's control.

<p class="contact">
<a href="mailto:{{ site.links.email }}">{{ site.links.email }}</a>
<a href="{{ site.links.scholar }}">Google Scholar</a>
{% if site.links.linkedin != "" %}<a href="{{ site.links.linkedin }}">LinkedIn</a>{% endif %}
{% if site.links.youtube != "" %}<a href="{{ site.links.youtube }}">YouTube</a>{% endif %}
<a href="/assets/cv.pdf">CV (PDF)</a>
</p>
</div>
</section>

## Research

<div class="pillars" markdown="1">
<div markdown="1">

### Perceptual manipulations and computational deception

Techniques that exploit the limits of human perception, such as redirected walking, can be misused to steer users without their awareness. We study these manipulations in XR, from false memories through source confusion to generative AI that produces deceptive designs on its own.

</div>
<div markdown="1">

### Engineering interaction for AI-driven XR

We build hardware and software for interaction, feedback and collaboration in AR and VR, from bringing non-HMD users into shared VR (ShareVR, FaceDisplay) to real-time generative models running on headset passthrough.

</div>
</div>

## Selected Publications

{% assign featured = site.data.publications | where: "featured", true %}
<div class="pubs">
{% for p in featured %}{% include publication.html pub=p %}{% endfor %}
</div>

<p class="more"><a href="/publications/">All publications</a></p>
