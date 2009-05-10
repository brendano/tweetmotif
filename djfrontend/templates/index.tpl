{% extends "base.tpl" %}

{% block content %}

<div id="logo_area">
  <table><tr><td>
  <a href="."><img border="0" src="static/img/logo.png"></a>
  <td>
  <div id="header_by_logo">Summarize any topic from the twitters.  <a href="about">More information.</a></div>
  </table>
</div>

<div>
  What are people saying about... &nbsp; 
  <input type="text" name="query" value="{{default_query}}" id="query"/><input type="button" name="search" value="Search" id="search">

  <img id="spinny" src="static/img/ajax-loader.gif" style="display:none">

  <div id="trends">
    {% if trend_topics %}
      Trending topics:
      {% for topic in trend_topics %}
        <a href="#" query="{{topic.simple_query}}" onclick="TT.trendClick($(this)); return false;">{{topic.name}}</a>
      {% endfor %}
      <br>
    {% endif %}
    Try:
      {% for q in prebaked_queries %}
        <a href="#" query="{{q}}" onclick="TT.trendClick($(this)); return false">{{q}}</a>
      {% endfor %}
  </div>
</div>

<div id='main'>
  <div id='resultswrapper'>
    <div id='resultscontent'><div class='content_header' style='display:none'><h2>results</h2> (click on a theme heading to drilldown)</div>
      <div id='resultsbytheme'></div>
    </div>
  </div>
  <div id='themelistcontainer'><div class='content_header' style='display:none'><h2>themes</h2></div>
    <ul id="themelist-col0"></ul>
    <ul id="themelist-col1"></ul>    
  </div>
</div>

<script type="text/javascript" charset="utf-8">
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
    
    this.clearThemeList = function() {
      $("#themelist-col0").html("");
      $("#themelist-col1").html("");
    }
    
    this.clearResults = function() {
      $("#themelist").empty();
      $("#resultsbytheme").empty();
      this.currentlyEnqueued = [];
      this.clearThemeList();
    }
    
    this.displayThemeList = function() {
      for (var i = 0; i < this.themeList.length; i++) {
        var curTheme = this.themeList[i];
        var whichCol = i % 2;
        $('<li><a href="#" theme="' + htmlQuote(curTheme) + '"' +  
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
    }
    this.startBusyGraphic = function() {
      $("#spinny").show();
    }
    this.stopBusyGraphic = function() {
      $("#spinny").hide();
    }
  }
  
  $(document).ready(function() {
    
    $("#query").keydown(function(e) {
      // console.log("query keydown: " + e.keyCode)
      if (e.keyCode == 13) {
        $("#search").click();
        return true;
      }
    });
    
    currentXHR = null;
    
    $("#search").click(function() {
      if (currentXHR && currentXHR.readyState != 0) {
        currentXHR.abort();
      }
      TT.startBusyGraphic();
      
      currentXHR = $.ajax({
        url: "do_query", data: {q: $("#query").val()},
        type: "GET", cache: false, dataType: "json",
        success: function(result) { 
          TT.stopBusyGraphic();
          TT.clearResults();
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
