{% extends "base.tpl" %}

{% block content %}

<div id="logo_area">
  <a href="/"><img border="0" src="static/img/logo.png"></a>
</div>


<p>TwitterThemes summarizes what's happening on Twitter.  It takes any word or phrase, <a href="http://search.twitter.com">finds tweets where people are talking about it</a>, then groups them by <a href="http://en.wikipedia.org/wiki/Language_model">statistically unlikely</a> <a href="http://en.wikipedia.org/wiki/Collocation_extraction">phrases</a> that <a href="http://en.wikipedia.org/wiki/Conditional_probability">co-occur</a> -- the themes of conversation.  By grouping tweets by theme, we give an overview of what people are saying and thinking.  
  
<p>You can dive deeper into a theme by clicking on it.  Our text analysis also clusters <a href="http://nlp.stanford.edu/IR-book/html/htmledition/near-duplicates-and-shingling-1.html">near-duplicates</a> and use other techniques to improve your view of twitterland.  If you want a straight-up list of tweet results, use the basic <a href="http://search.twitter.com/">search.twitter.com</a>.

<p>TwitterThemes was created by <a href="http://anyall.org/">Brendan O'Connor</a> (<a class="at" href="http://twitter.com/brendan642">@brendan642</a>), <a href="http://staff.science.uva.nl/~ahn/">David Ahn</a> (<a class="at" href="http://twitter.com/davidahn">@davidahn</a>) and <a href="http://hci.stanford.edu/mkrieger/">Mike Krieger</a> (<a class="at" href="http://twitter.com/mikeyk">@mikeyk</a>).  We put it up this week.
  
<p>Please send us feedback!  On Twitter reply to <a href="http://twitter.com/home?status=@brendan642+%23twitterthemes ">@brendan642 #twitterthemes</a>, or else email at <a href="mailto:brenocon@gmail.com">brenocon@gmail.com</a>.
  
{% endblock %}
