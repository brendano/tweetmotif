{% extends "base.tpl" %}

{% block extrahead %}
	<link rel="stylesheet" href="static/css/trends-web.css" type="text/css" media="screen" title="no title" charset="utf-8">
{% endblock %}

{% block content %}

<div id="logo_area">
  <div id="header_by_logo"><a target="_blank" href="http://twitter.com/home?status=Summarize%20any%20Twitter%20topic%20at%20http%3A%2F%2Ftwittermotif.com">(tweet this)</a> <a href="about">(about)</a> <a href="#" onclick='TT.showTips(); return false'>(tips)</a></div>	
  <a href="#"><img border="0" src="static/img/bird-logo.png"></a>
</div>

<div id="content">
<div id ="searcharea">
  What are people saying about... &nbsp; 
  <input type="text" name="query" value="{{default_query}}" id="query"/><input type="button" name="search" value="Search" id="search">

  <img id="spinny" src="static/img/ajax-loader.gif" style="display:none">

  <div id="trends">
    {% if trend_topics %}
	<div id="trending-topics" class="prefill-suggestions">
      <h3>Trending topics</h3>

      {% for topic in trend_topics %}
        <a href="#" query="{{topic.simple_query}}" onclick="TT.trendClick($(this)); return false;">{{topic.name}}</a>{% if not forloop.last  %}
        	&bull;
        {% endif %}
      {% endfor %}
	</div>
    {% endif %}
   <div id="suggested-searches" class="prefill-suggestions">
	 <h3>Try</h3>
      {% for q in prebaked_queries %}
        <a href="#" query="{{q}}" onclick="TT.trendClick($(this)); return false">{{q}}</a>{% if not forloop.last  %}
        	&bull;
        {% endif %}
      {% endfor %}
	</div>
  </div>
</div>

<div id='main'>
  <div id='resultswrapper'>
    <div id='resultscontent'><div class='content_header' id="tweets-by-theme-title" style='display:none'><h2>tweets by theme</h2></div>
      <div id='resultsbytheme'></div>
    </div>
  </div>
  <div id='themelistcontainer'><div class='content_header' id="related-themes-title" style='display:none'><h2>related themes</h2><div id='timeInfo' style='display:none'></div></div>
    <ul id="themelist-col0"></ul>
    <ul id="themelist-col1"></ul>    
  </div>
</div>

</div>

<div id="tips">
	<ul>
		<li>Choose a trending topic, suggested query, or your own search.</li>
		<li>Then choose a theme from the left column.</li>
		<li>Tweets will be shown on the right, grouped by theme.</li>
		<li>Click on a theme name to drill-down on that theme.</li>
	</ul>
		
</div>

<script type="text/javascript" charset="utf-8">

</script>

{% endblock %}
