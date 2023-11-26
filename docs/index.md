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

# More Stuff From Me

## Medium

If you find this resource useful, you might like to check out some of my other content. On **[Medium](https://medium.com/@derailed.dash){:target="_blank"}** I routinely write articles on blogs on topics such as:

- [Architecture Documentation: Where to Draw the Line](https://medium.com/@derailed.dash/architecture-documentation-where-to-draw-the-line-df73fb5ca85c){:target="_blank"}
- [My Series on Google Cloud Adoption: from Strategy to Operation](https://medium.com/google-cloud/google-cloud-adoption-for-the-enterprise-from-strategy-to-operation-part-0-overview-9091f5a1ddfc){:target="_blank"}
- [Google Cloud Landing Zones with Google Cloud Foundation Fabric FAST](https://medium.com/google-cloud/google-cloud-landing-zone-with-terraform-and-cloud-foundation-fabric-fast-part-1-2c7634ac31fd){:target="_blank"}
- [Terraforming an Application on Google Cloud](https://medium.com/google-cloud/a-sample-application-using-terraform-on-google-cloud-2405c598a60a){:target="_blank"}
- [Google Cloud Next Summaries, and Announcements](https://medium.com/google-cloud/google-next-2023-experience-and-favourite-sessions-fb00add5f59e){:target="_blank"}
- [Getting More from ChatGPT](https://medium.com/@derailed.dash/a-couple-of-tools-to-get-more-from-chatgpt-7847e21aac05){:target="_blank"}

I would really appreciate if you would **Follow Me** on Medium, and share any content that you think would be useful to your friends and colleauges.

## My Advent of Code Walkthroughs Site

Check out my [Learning Python with Advent of Code Walkthroughs resource](https://aoc.just2good.co.uk/){:target="_blank"}.

## GitHub

Finally, consider:

- [Following me on GitHub](https://github.com/derailed-dash){:target="_blank"}
- [Adding a Star to my Advent-of-Code GitHub Repo, or any other repos you find useful](https://github.com/derailed-dash/Advent-of-Code){:target="_blank"}