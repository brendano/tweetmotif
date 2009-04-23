if (typeof(console) == "undefined") {
  console = {}
  console.log = function() { }
}

jQuery.query = function() { 
        var r = {}; 
        var q = location.search;        
        q = q.replace(/^\?/,''); // remove the leading ?        
        q = q.replace(/\&$/,''); // remove the trailing & 
        jQuery.each(q.split('&'), function(){ 
                var key = this.split('=')[0]; 
                var val = this.split('=')[1]; 
                // convert floats 
                if(/^[0-9.]+$/.test(val)) 
                        val = parseFloat(val); 
                // ingnore empty values 
                if(val) 
                        r[key] = val; 
        }); 
        return r; 
}; 

function topic_click(elt) {
  var topic_label = $(elt).html()
  // console.log(topic_label)
  var topic = topics[topic_label]
  var has_been_requeried = topic.requery_tweets_html ? true : false
  if (has_been_requeried) {
    var html = topic.requery_tweets_html
  } else {
    var html = topic.tweets_html
    html += "<hr><img src=http://blog-well.com/wp-content/uploads/2007/06/bar-circle.gif>"
  }
  $("#tweets").html( html )
  if (!has_been_requeried)
    requery(topic_label)
  $(".topic_label.sel").removeClass("sel")
  $(elt).addClass("sel")
}

function requery(topic_label) {
  $.get(".", {single_query:1, q:$.query().q, topic_label:topic_label},
  function(data,text) { 
    topics[topic_label].requery_tweets_html = data
    $("#tweets").html(data)
  })
}
function jsonp_insert(search_results) {
  var tweets = search_results.results;
  // console.log(tweets)
  var h = ""
  for (var i=0; i<tweets.length; i++) {
    h += tweets[i].text + "<br>"
  }
  $("#tweets").html(h)
}

