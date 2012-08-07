/*jshint browser:true, devel:true, node:true*/
/*global
Backbone: false
_: false
define: false
*/
//"use strict";
define([
  // Application.
  "app",

  // Libs
  "backbone"
],

// Map dependencies from above array.
function(app, Backbone) {

  // Create a new module.
  var CouchView = app.module();

  // Default model.
  CouchView.Model = Backbone.Model.extend({
    initialize: function(doc) {  }
  });

  // Default collection.
  CouchView.Collection = Backbone.Collection.extend({
    model: CouchView.Model,
    url: 'highscore',
    stale: "ok",
    success: function(result){
      // Make a list of models to add into the collection
      var models = [];
      _.each( result.rows, function( row ) {
        if(row){
          models.push( row );
        }
      });
      if ( models.length === 0 ) { models = null; }
      return models;
    },
    error : function(jqXHR, textStatus, errorThrown){
      Backbone.couch.log(["jqXHR", jqXHR]);
      Backbone.couch.log(["textStatus", textStatus]);
      Backbone.couch.log(["errorThrown", errorThrown]);
      return null;
    }
  });

  // Return the module for AMD compliance.
  return CouchView;

});
