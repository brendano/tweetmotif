<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN">
<html>
  <head>

    <title></title>
    <script type="text/javascript" charset="utf-8">
      if (!window['console']) {
        window.console = {};
        window.console.log = function(){};
      }
    </script>
    <script src="static/js/jquery-1.3.2.min.js" type="text/javascript" charset="utf-8"></script>
    <script type="text/javascript" charset="utf-8">

    </script>
    <link rel="stylesheet" href="static/css/trends.css" type="text/css" media="screen" title="no title" charset="utf-8"/>
  </head>
  <body>  
    {% block content %}
      
    {% endblock %}

		<script type="text/javascript">
		var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
		document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));
		</script>
		<script type="text/javascript">
		try {
		var pageTracker = _gat._getTracker("UA-8800458-1");
		pageTracker._trackPageview();
		} catch(err) {}</script>
  </body>
</html>
