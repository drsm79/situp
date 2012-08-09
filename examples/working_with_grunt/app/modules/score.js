/*jshint browser:true, devel:true, node:true, jquery: true*/
/*global
Backbone: false
_: false
define: false
CouchView: false
*/
//"use strict";
define([
  // Application.
  "app",

  // Libs
  "backbone",
  "modules/CouchView"
],

// Map dependencies from above array.
function(app, Backbone, CouchView) {

  // Create a new module.
  var Score = app.module();

  // Default collection.
  Score.Collection = CouchView.Collection.extend({
    // Collection of scores, limited to top 10
    doreduce: false,
    descending: true,
    limit: 10,
    parse: function(response){
      return _.map(response, function(row){
        return {player: row.value, score: row.key[1]};
      });
    },
    setGame: function(game){
      // Set the game in the view parameters
      this.startkey = [game, {}];
      this.endkey = [game];
    }
  });

  Score.View = Backbone.View.extend({
    initialize: function(settings) {
      // Bind functions to actions
      _.bindAll(this);
      this.collection.bind('change', this.render);
      this.collection.bind('add', this.render);
      this.collection.bind('remove', this.render);
      this.collection.bind('reset', this.render);
      console.log('Score instance up');
    },
    render: function() {
      // Define how the collection is rendered into the page
      var table = $('<ul></ul>');
      this.collection.each(function(doc){
        table.append('<li>' + doc.get('score') + ' : ' + doc.get('player') + '</li>');
      });
      $('.scores').html('<h2>' + this.game + '</h2>');
      $('.scores').append(table);
    },
    setGame: function(game){
      // Set the game in the view and collection then fetch the collection
      this.game = game;
      this.collection.setGame(game);
      this.collection.fetch();
    }

  });

  // Return the module for AMD compliance.
  return Score;

});
