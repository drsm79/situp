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
  var Game = app.module();

  // Default collection.
  Game.Collection = CouchView.Collection.extend({
    doreduce: true,
    group_level: 1,
    group: true,
    parse: function(response){
      return _.map(response, function(row){
        return {name: row.key[0]};
      });
    }
  });

  Game.View = Backbone.View.extend({
    initialize: function(settings) {
      // Bind functions to actions, store the scores object
      _.bindAll(this);
      this.collection.bind('change', this.render);
      this.collection.bind('add', this.render);
      this.collection.bind('remove', this.render);
      this.collection.bind('reset', this.render);
      this.scores = settings.scores;
      this.collection.fetch();
      console.log('Game instance up');
    },
    render: function() {
      // Define how the collection is rendered into the page
      var dropdown = $('<select></select>');
      var that = this; // needed for the change event below

      //console.log(this.foo);
      //console.log(this.scores);
      //console.log(that.scores);

      this.collection.each(function(game){
        dropdown.append('<option>' + game.get('name') + '</option>');
      });
      $('.games').html(dropdown);

      this.scores.setGame($('.games select :selected').text());

      // When the dropdown changes set the game for the scores collection,
      // triggering it's render function.
      $('.games select').change(function(event){
        that.scores.setGame($('.games select :selected').text());
      });
    }
  });

  // Return the module for AMD compliance.
  return Game;

});
