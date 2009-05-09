if (typeof(console) == "undefined") {
  console = {}
  console.log = function() { }
}

// jQuery.query = function() { 
//         var r = {}; 
//         var q = location.search;        
//         q = q.replace(/^\?/,''); // remove the leading ?        
//         q = q.replace(/\&$/,''); // remove the trailing & 
//         jQuery.each(q.split('&'), function(){ 
//                 var key = this.split('=')[0]; 
//                 var val = this.split('=')[1]; 
//                 // convert floats 
//                 if(/^[0-9.]+$/.test(val)) 
//                         val = parseFloat(val); 
//                 // ingnore empty values 
//                 if(val) 
//                         r[key] = val; 
//         }); 
//         return r; 
// }; 

// function topic_click_unified(elt) {
//   var topic_label = $(elt).attr('topic_label')
//   // console.log(topic_label)
//   var topic = topics[topic_label]
//   var has_been_requeried = topic.requery_tweets_html ? true : false
//   if (has_been_requeried) {
//     var html = topic.requery_tweets_html
//   } else {
//     var html = topic.tweets_html
//     html += "<hr><img class=loading src=http://anyall.org/twistatic/ajax-loader.gif>"
//   }
//   $("#tweets").html( html )
//   if (!has_been_requeried)
//     requery(topic_label)
//   $(".topic_label.sel").removeClass("sel")
//   $(elt).addClass("sel")
// }

function topic_click(elt) {
  var topic_label = $(elt).attr('topic_label')
  var topic = topics[topic_label]
  $("#tweets").html( topic.tweets_html )
  var has_been_requeried = topic.requery_tweets_html ? true : false
  if (has_been_requeried) {
    $("#tweets_more").html(topic.requery_tweets_html)
  } else {
    $("#tweets_more").html("<img class=loading src=http://anyall.org/twistatic/ajax-loader.gif>")
    requery(topic_label)
  }
  $(".topic_label.sel").removeClass("sel")
  $(elt).addClass("sel")
}

function requery(topic_label) {
  $.ajax({url:"backend", type:"GET", 
    data:{single_query:1, q:$.query.keys.q, topic_label:topic_label, exclude:topics[topic_label].tweet_ids},
    dataType:"html",
    success: function(data,text) { 
      topics[topic_label].requery_tweets_html = data
      $("#tweets_more").html(data)
    },
    error: function(xhr, text, error) {
      $("img.loading").attr("src","http://anyall.org/twistatic/ajax-loader-stopped.gif")
      console.log(text)
      console.log(xhr)
    }
})
  // $.get(".", {single_query:1, q:$.query().q, topic_label:topic_label},
  // function(data,text) { 
    // topics[topic_label].requery_tweets_html = data
    // $("#tweets").html(data)
  // })
}

function load_default_topic() {
  topic_click($('.topic_label')[0])
}
