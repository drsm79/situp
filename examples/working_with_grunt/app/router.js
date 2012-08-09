define([
  // Application.
  "app",

  // Modules.
  "modules/score",
  "modules/game"
],
//Order matters here!
function(app, Score, Game) {

  // Defining the application router, you can attach sub routers here.
  var Router = Backbone.Router.extend({
    routes: {
      "": "index"
    },

    index: function() {
      // Initialise the app
    },
    initialize: function(options) {
      var pieces = window.location.pathname.split('/_design/');
      // Set database and design doc based on URL
      Backbone.couch.databaseName = pieces[0].replace('/', '');
      Backbone.couch.ddocName  = pieces[1].split('/')[0];
      Backbone.couch.enableChangesFeed = false;
      app.games = new Game.View({
        collection: new Game.Collection(),
        scores: new Score.View({collection: new Score.Collection()})
      });

    }
  });

  return Router;

});
