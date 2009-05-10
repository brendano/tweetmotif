{% extends "base.tpl" %}

{% block content %}
<div id="logo_area">
  <img src="static/img/logo.png">
</div>

<div>
What are people saying about... &nbsp; <input type="text" name="query" value="dogs" id="query"/><input type="button" name="search" value="Search" id="search">
</div>

<div id='main'>
  <div id='resultswrapper'>
    <div id='resultscontent'><h2>results</h2>
      <div id='resultsbytheme'></div>
    </div>
  </div>
  <div id='themelistcontainer'><h2>themes</h2>
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
  twitterThemes = new function() {
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
    
    this.displayThemeList = function(){
      for (var i = 0; i < this.themeList.length; i++) {
        var curTheme = this.themeList[i];
        var whichCol = i % 2;
        $('<li><a href="#" theme="' + htmlQuote(curTheme) + '"' +  
            'onclick="twitterThemes.enqueueTheme($(this).attr(\'theme\')); return false">' + 
            labelHtml(curTheme) + '</a></li>').appendTo("#themelist-col" + whichCol);
      }
    }
    
    this.showMoreFor = function(id) {
      $(".extratweets", "#tweetresult-" + id).slideDown("normal");
      $(".slidedownlink", "#tweetresult-" + id).hide();
    }
    
    this.tellNoResults = function() {
      $("#resultsbytheme").html("No results for this query.");
    }
    
    this.enqueueTheme = function(theme) {
      var currentPosition = -1;
      for (var i = 0; i < this.currentlyEnqueued.length; i++) {
        if (this.currentlyEnqueued[i] == theme) {
          currentPosition = i;
        }
      }
      if (currentPosition != -1 && currentPosition != 0) {
        // console.log($("#resultscontent").contents()[currentPosition]);
        var elem = $("#resultsbytheme").contents()[currentPosition];
        $(elem).remove();
        this.currentlyEnqueued.splice(currentPosition, 1);
        
      } else if (currentPosition == 0) {
        return;
      }
      this.currentlyEnqueued.unshift(theme);
      var themeData = this.data[theme];
      var themeHtml = (theme=="**EXTRAS**") ? ""   //"<i>tweets on other themes...<i>" : 
          : "<h3>&ldquo;" + labelHtml(theme) + "&rdquo;</h3>";
      var tweetList = $("<div class='theme'><h3>" + themeHtml + "</h3></div>");
      for (var i = 0; i < themeData.groups.length; i++) {
        var group = themeData.groups[i];
        var thisTweet = $("<div class='tweet'>" + group.head_html + "</div>").appendTo(tweetList);
        if (group.rest_htmls.length > 0) {
          var n = group.rest_htmls.length
          var t = pluralize("tweet", n)
          // todo clicky
          thisTweet = $("<div class='rest_tweets'>" + n + " similar " + t + "...</div>").appendTo(tweetList);
        }
        if (i > this.tweetsPerResult) {
          thisTweet.addClass("extratweets");
        }
      }
      tweetList.hide();
      var safeThemeName = theme.replace(/ /g, "_");
      tweetList.attr("id", "tweetresult-" + (safeThemeName));
      tweetList.append('<div><a class="slidedownlink" href="#" onclick="twitterThemes.showMoreFor(\'' + 
        jsStringQuote(safeThemeName) +'\'); return false">See more</a></div>');
      $("#resultsbytheme").prepend(tweetList);
      tweetList.slideDown("normal");
      if ($("#resultsbytheme").contents().length > this.blocksToEnqueue) {
        $($("#resultsbytheme").contents()[this.blocksToEnqueue]).slideUp();
      }
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
    $("#search").click(function(){
      // console.log("search click")
      $.getJSON('do_query',{
          q: $("#query").val()},
        function(result) {
          twitterThemes.clearResults()
          twitterThemes.themeList = result.topic_list;
          twitterThemes.data = result.topic_info;
          if (twitterThemes.themeList.length == 0) {
            twitterThemes.tellNoResults();
            return;
          }
          twitterThemes.displayThemeList();
          for (var i = Math.min(2, twitterThemes.themeList.length-1); i >= 0; i--) {
            twitterThemes.enqueueTheme(twitterThemes.themeList[i])
          }
      });
      
    })
    
  });

</script>

{% endblock %}
