{% extends "base.tpl" %}

{% block extrahead %}
<script type="text/javascript" charset="utf-8">
		TT.blocksToEnqueue = 1;
		TT.maxTopics = 10;
		TT.numColumns = 1;
		TT.isPhone = true;		
</script>
		<meta name="viewport" content="width=240, user-scalable=no"/>
		<link rel="stylesheet" href="static/css/trends-iphone.css" type="text/css" media="screen" title="no title" charset="utf-8">
{% endblock %}

{% block content %}
	<div id="header">
		<img src="static/img/bird-logo-iphone.jpg" style="width:100%"/>
	</div>
	
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
	<div id="searchbox">
	<input type="text" id="query" /><br/> <input type="button" id="search" value="Search"><br/>
	  <img id="spinny" src="static/img/ajax-loader.gif" style="display:none">	
	</div>



 
	
	
	<div id='main'>
	  <div id='themelistcontainer'><div class='content_header' style='display:none'><h2>related topic results</h2></div>
	    <ul id="themelist-col0"></ul>  
	  </div>
		
	  <div id='resultswrapper'>
	    <div id='resultscontent'><div class='content_header' style='display:none'></div>
	      <div id='resultsbytheme'></div>
	    </div>
	  </div>
	</div>
	
	</div>
	<a id="new-search-link" href="#" onclick='window.location.hash="";$(this).hide();$("#query").focus()'>Start new search</a>
{% endblock %}