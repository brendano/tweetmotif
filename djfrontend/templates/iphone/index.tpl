{% extends "base.tpl" %}

{% block extrahead %}
<script type="text/javascript" charset="utf-8">
		TT.blocksToEnqueue = 1;
		TT.maxTopics = 10;
		TT.numColumns = 1;
		TT.isPhone = true;	
		$(document).ready(function(){
			$("#searchform").submit(function(event){
					event.preventDefault();
					event.stopPropagation();
					$("#search").click();
					$("#header").focus();
			})	
			
		})
</script>
		<meta name="viewport" content="width=device-width, user-scalable=no"/>
		<link rel="stylesheet" href="static/css/trends-iphone.css" type="text/css" media="screen" title="no title" charset="utf-8">
{% endblock %}

{% block content %}
	<div id="header">
		<a href="#" onclick='window.location.hash="";return false; $("#query").focus()'>
		<img src="static/img/bird-logo-iphone.jpg" style="width:100%"/>
		</a>
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
</div>
<form id="searchform">
	<div id="searchbox">
	<input type="text" id="query" placeholder="Enter your query" /><br/> <input type="button" id="search" value="Search"><br/>
	  <img id="spinny" src="static/img/ajax-loader.gif" style="display:none">	
	</div>
</form>


 
	
	
	<div id='main'>
	  <div id='themelistcontainer'><div class='content_header' style='display:none'><h2>Related topic results</h2></div>
	    <ul id="themelist-col0"></ul>  
	  </div>
		
	  <div id='resultswrapper'>
	    <div id='resultscontent'><div class='content_header' style='display:none'></div>
	      <div id='resultsbytheme'></div>
	    </div>
	  </div>
	</div>
	
	<a id="new-search-link" href="#" onclick='window.location.hash="";$(this).hide();$("#query").focus()'>Start new search</a>
{% endblock %}