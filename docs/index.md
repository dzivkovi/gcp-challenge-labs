---
layout: default
title: Main
---
# Quests and Challenge Labs

Google provides an online learning platform called Google [Cloud Skills Boost](https://www.cloudskillsboost.google/){:target="_blank"}, formerly known as QwikLabs.

On this platform, you can follow training courses aligned to learning paths, particular products, or particular solutions.

One type of learning experience on this platform is called a **quest**.  This is where you complete a number of guided hands-on labs, and then finally complete a **Challenge Lab**. The **challenge lab** differs from the other labs in that goals are specified, but very little guidance on _how_ to achieve the goals is given.

Here I'll document my experience with some of these challenge labs.

<ul>
  {% assign the_year = site.data.navigation.pages | where: 'name', 'Main' %}
  {% for member in the_year[0].members %}
      <li><a href="{{ member.link | absolute_url }}">{{ member.name }}</a></li>
  {% endfor %}
</ul>