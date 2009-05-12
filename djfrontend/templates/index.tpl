{% extends "base.tpl" %}

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
    <div id='resultscontent'><div class='content_header' style='display:none'><h2>tweets by theme</h2></div>
      <div id='resultsbytheme'></div>
    </div>
  </div>
  <div id='themelistcontainer'><div class='content_header' style='display:none'><h2>related themes</h2></div>
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

	jQuery.fn.fadeToggle = function(speed, easing, callback) {
	   return this.animate({opacity: 'toggle'}, speed, easing, callback);

	};

  
  function labelHtml(label) {
    if (label == "**EXTRAS**") return "<i>more...</i>"
    return htmlQuote(label);
    // return htmlQuote(label).replace(/ /g,"&nbsp;");
  }
  function htmlQuote(s) {
    return s.replace(/"/g, "&quot;").replace(/>/g, "&gt;").replace(/</g,"&lt;");
  }
  function jsStringQuote(s) {
    return s.replace(/'/g, "\\'").replace(/"/g,'\\"');
  }
  function pluralize(s, n, /*optional*/ suffix) {
    if (n == 1) return s;
    if (suffix==undefined)  suffix = "s"
    return s + suffix;
  }
  
  TT = new function() {
    this.blocksToEnqueue = 3;
    this.data = {};
    this.tweetsPerResult = 4;
    this.currentlyEnqueued = [];

		this.showTips = function(){
			$("#tips").fadeToggle("true");
		}
    
    this.clearThemeList = function() {
      $("#themelist-col0").html("");
      $("#themelist-col1").html("");
    }
    
    this.clearResults = function(animate) {		
	
			var callback = function(){
	      $("#themelist").empty();
	      $("#resultsbytheme").empty();
	      TT.currentlyEnqueued = [];
	      TT.clearThemeList();
			}
	
			if (animate) {
				$("#main").hide();
				callback();
			} else {
				$("#main").hide();
				callback();
			}
    }
    
    this.displayThemeList = function() {
      for (var i = 0; i < this.themeList.length; i++) {
        var curTheme = this.themeList[i];
        var whichCol = i % 2;
        $('<li><a class="themelink" href="#" theme="' + htmlQuote(curTheme) + '"' +  
            'onclick="TT.enqueueTheme($(this).attr(\'theme\')); return false">' + 
            labelHtml(curTheme) + '</a></li>').appendTo("#themelist-col" + whichCol);
      }
    }
    
    this.showMoreFor = function(id) {
      $(".extratweets", "#tweetresult-" + id).slideDown("normal");
      $(".slidedownlink", "#tweetresult-" + id).hide();
    }
    
    this.tellNoResults = function() {
      $("#resultsbytheme").html("<br>No results for this query.");
    }
    
    this.trendClick = function(elt) {
      console.log(elt.attr('query'))
      $("#query").attr('value',elt.attr('query'));
      $("#search").click();
    }
    
    this.newsearchClick = function(elt) {
      var theme = $(elt).attr('theme');
      var new_q = TT.data[theme].query_refinement;
      $("#query").attr('value', new_q)
      $("#search").click()
    }
    
    this.rest_tweets_click = function(elt) {
      elt.parents('.tweet').next('.rest_tweets').toggle('normal', function() {
        var vis = $(this).is(':visible');
        if (vis) {
          elt.html(elt.html().replace("show","hide").replace("»","«"));
        } else {
          elt.html(elt.html().replace("hide","show").replace("«","»"));
        }
        return true;
      })
    }
    
    this.enqueueTheme = function(theme) {
      var currentPosition = -1;
      for (var i = 0; i < this.currentlyEnqueued.length; i++) {
        if (this.currentlyEnqueued[i] == theme) {
          currentPosition = i;
        }
      }
      if (currentPosition != -1 && currentPosition != 0) {
        var elem = $("#resultsbytheme").contents()[currentPosition];
        $(elem).remove();
				this.currentlyEnqueued.splice(currentPosition, 1);
        
      } else if (currentPosition == 0) {
        return;
      }
      this.currentlyEnqueued.unshift(theme);
			this.currentlyEnqueued.splice(this.blocksToEnqueue,1);

      var themeData = this.data[theme];
      var themeHtml = (theme=="**EXTRAS**") ? ""   //"<i>tweets on other themes...<i>" : 
          : "&ldquo;" + labelHtml(theme) + "&rdquo;";
      var newsearch_tag = "<span class='newsearch' theme='" + labelHtml(theme) + "' onclick='TT.newsearchClick($(this)); return false;'>"
      var tweetList = $("<div class='theme'>" + newsearch_tag + themeHtml + "</span></div>");
      for (var i = 0; i < themeData.groups.length; i++) {
        var group = themeData.groups[i];
        var head_html = "<div class='tweet'>" + group.head_html;
        var rest_html = "";
        if (group.rest_htmls.length > 0) {
          head_html += " ";
          var n = group.rest_htmls.length;
          var t = pluralize("tweet", n);
          head_html += " &nbsp; <span class='rest_tweets_msg'><a href='#' onclick='TT.rest_tweets_click($(this)); return false;'>show " + n + " similar " + t + " »</a></span>";
          
          rest_html += "<div class='rest_tweets' style='display:none'>";
          for (var j=0; j < group.rest_htmls.length; j++) {
            rest_html += "<div class='rest_tweet'>" + group.rest_htmls[j] + "</div>";
          }
          rest_html += "</div>"
        }
        head_html += "</div>";
        $(head_html + rest_html).appendTo(tweetList);
        
        // if (false &&  i > this.tweetsPerResult) {
        //   console.log("never here now.")
        //   thisTweet.addClass("extratweets");  // whoa .. all elements would get this? 
        // }
      }
      tweetList.hide();
      var safeThemeName = theme.replace(/ /g, "_");
      tweetList.attr("id", "tweetresult-" + (safeThemeName));
      // tweetList.append('<div><a class="slidedownlink" href="#" onclick="TT.showMoreFor(\'' + 
      //         jsStringQuote(safeThemeName) +'\'); return false">See more</a></div>');
      $("#resultsbytheme").prepend(tweetList);
      tweetList.slideDown("normal");
      if ($("#resultsbytheme").contents().length > this.blocksToEnqueue) {
        $($("#resultsbytheme").contents()[this.blocksToEnqueue]).slideUp();
      }

			for (var i=0; i < $(".themelink").length; i++) {
				var curElem = $($(".themelink")[i]);
				var isSelectedTheme = false;				
				for (var j=0; j < this.currentlyEnqueued.length; j++) {
					if (this.currentlyEnqueued[j] == curElem.text()) {
						isSelectedTheme = true;
					} 
				};
				if (isSelectedTheme) {
					curElem.addClass("selected-theme");									
				} else {
					curElem.removeClass("selected-theme");
				}
			};
    }
   this.startBusyGraphic = function() {
     $("#spinny").show();
   }
   this.stopBusyGraphic = function() {
     $("#spinny").hide();
   }
 

	this.currentQuery = "";

	this.checkHash = function(){
		var hash = window.location.hash.substring(1);

		// var hash = hash);
		if (TT.currentQuery != "" && (hash == "" || hash == "#")) {
			// console.log("EMPTYYY");
			TT.currentQuery = "";
			window.location.hash = "";
			TT.clearResults();
			$("#query").val("");
		} else if (TT.currentQuery != hash){
			TT.currentQuery = hash;
			// var evt = {'target':{'id':'item-'hashAsInt}};
			$("#query").val(decodeURIComponent(hash));
			$("#search").click();
		}
	}
	
}	

  $(document).ready(function() {
    
		setInterval(TT.checkHash, 400);

    $("#query").keydown(function(e) {
      // console.log("query keydown: " + e.keyCode)
      if (e.keyCode == 13) {
        $("#search").click();
        return true;
      }
    });
    
    currentXHR = null;
    
    $("#search").click(function() {

      var query = $("#query").val();

			if (query == this.currentQuery) return;

      if (currentXHR && currentXHR.readyState != 0) {
        currentXHR.abort();
      }
      TT.startBusyGraphic();


			window.location.hash = encodeURIComponent(query);

			TT.clearResults(true);
			this.currentQuery = query;
      currentXHR = $.ajax({
        url: "do_query", data: {q: query},
        type: "GET", cache: false, dataType: "json",
        success: function(result) { 
					$("#main").show();
          TT.stopBusyGraphic();
          // TT.clearResults();
          $('.content_header').show()
          TT.themeList = result.topic_list;
          TT.data = result.topic_info;
          if (TT.themeList.length == 0) {
            TT.tellNoResults();
            return;
          }
          TT.displayThemeList();
          for (var i = Math.min(2, TT.themeList.length-1); i >= 0; i--) {
            TT.enqueueTheme(TT.themeList[i])
          }
        },
        error: function(xhr, text, err) {
          TT.stopBusyGraphic();
          console.log(err + " -- " + text) 
        }
      })
      
    });
    
  });
  

</script>

{% endblock %}
