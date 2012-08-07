/*jshint browser:true, devel:true, node:true, jquery: true*/
/*global
Backbone: false
_: false
require: false
Score: false
Game: false
*/
require([
  // Application.
  "app",

  // Main Router.
  "router",

  // Modules.
  "modules/score",
  "modules/game"
],

function(app, Router, Game, Score) {

  // Define your master router on the application namespace and trigger all
  // navigation from this instance.
  app.router = new Router();

  // Trigger the initial route and enable HTML5 History API support, set the
  // root folder to '/' by default.  Change in app.js.
  Backbone.history.start({ pushState: true, root: app.root });

  // All navigation that is relative should be passed through the navigate
  // method, to be processed by the router. If the link has a `data-bypass`
  // attribute, bypass the delegation completely.
  $(document).on("click", "a:not([data-bypass])", function(evt) {
    // Get the absolute anchor href.
    var href = $(this).attr("href");

    // If the href exists and is a hash route, run it through Backbone.
    if (href && href.indexOf("#") === 0) {
      // Stop the default event to ensure the link will not cause a page
      // refresh.
      evt.preventDefault();

      // `Backbone.history.navigate` is sufficient for all Routers and will
      // trigger the correct events. The Router's internal `navigate` method
      // calls this anyways.  The fragment is sliced from the root.
      Backbone.history.navigate(href, true);
    }
  });
  // Initialise the app
  var pieces = window.location.pathname.split('/_design/');
  // Set database and design doc based on URL
  Backbone.couch.databaseName = pieces[0].replace('/', '');
  Backbone.couch.ddocName  = pieces[1].split('/')[0];
  Backbone.couch.enableChangesFeed = false;
  app.games = new Game.View({
    collection: new Game.Collection(),
    scores: new Score.View({collection: new Score.Collection()})
  });
});
