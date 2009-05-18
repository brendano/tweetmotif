{% extends "base.tpl" %}

{% block content %}

<div id="logo_area">
  <a href="."><img border="0" src="static/img/bird-logo.png"></a>
</div>

<div id='content'>

<p>TweetMotif summarizes what's happening on Twitter.  It takes any word or phrase, <a href="http://search.twitter.com">finds tweets where people are talking about it</a>, then groups them by <a href="http://en.wikipedia.org/wiki/Language_model">statistically unlikely</a> <a href="http://en.wikipedia.org/wiki/Collocation_extraction">phrases</a> that <a href="http://en.wikipedia.org/wiki/Conditional_probability">co-occur</a> &ndash; the themes of the conversation.  

<p>By grouping tweets, we give an overview of what people are saying and thinking.  Our text analysis system also clusters <a href="http://nlp.stanford.edu/IR-book/html/htmledition/near-duplicates-and-shingling-1.html">near-duplicates</a> and uses other techniques to improve your view of the twitterlands.

<p>TweetMotif is an experiment created by <a href="http://anyall.org/">Brendan O'Connor</a> (<a class="at" href="http://twitter.com/brendan642">@brendan642</a>), <a href="http://staff.science.uva.nl/~ahn/">David Ahn</a> (<a class="at" href="http://twitter.com/davidahn">@davidahn</a>) and <a href="http://ambientwitter.appspot.com/">Mike Krieger</a> (<a class="at" href="http://twitter.com/mikeyk">@mikeyk</a>).  We released it last week.

<p><a target="_blank" href="http://twitter.com/home?status=Summarize%20any%20Twitter%20topic%20at%20http%3A%2F%2Ftweetmotif.com">Tweet this!</a>
  
<p>And please give us feedback!  At <a class="at" href="http://twitter.com/tweetmotif">@tweetmotif</a>, or email at <a href="mailto:tweetmotif@gmail.com">tweetmotif@gmail.com</a>.

</div>

{% endblock %}
